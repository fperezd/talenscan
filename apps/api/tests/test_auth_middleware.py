"""Tests del middleware de API key (hardening interino).

Verifica: desactivado si no hay key; cuando hay key, exige X-API-Key en /api
admin pero deja pasar /health y /api/public/*.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import settings as security_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_no_key_means_open(client, monkeypatch):
    monkeypatch.setattr(security_settings, "api_key", "")
    # /health siempre abierto
    assert client.get("/health").status_code == 200


def test_key_required_on_admin(client, monkeypatch):
    monkeypatch.setattr(security_settings, "api_key", "secret-123")
    # Sin header → 401
    resp = client.get("/api/mandatos")
    assert resp.status_code == 401
    assert "API key" in resp.json()["detail"]
    # Con header correcto → pasa el middleware (200 o error de DB, pero no 401)
    ok = client.get("/api/mandatos", headers={"X-API-Key": "secret-123"})
    assert ok.status_code != 401
    # Header incorrecto → 401
    bad = client.get("/api/mandatos", headers={"X-API-Key": "nope"})
    assert bad.status_code == 401


def test_public_and_health_exempt_even_with_key(client, monkeypatch):
    monkeypatch.setattr(security_settings, "api_key", "secret-123")
    assert client.get("/health").status_code == 200
    # /api/public/* exento (token inexistente → 404/410, pero NO 401 por API key)
    resp = client.get("/api/public/shortlists/token-inexistente")
    assert resp.status_code != 401


def test_auth_endpoints_exempt_even_with_key(client, monkeypatch):
    # Las puertas de entrada (login/registro/SSO callback) no deben requerir
    # el API key — el callback OAuth lo invoca el navegador sin headers.
    monkeypatch.setattr(security_settings, "api_key", "secret-123")
    resp = client.post("/api/auth/login", json={"email": "x@empresa.com", "password": "nope"})
    # 401 por credenciales, NO por API key → significa que pasó el middleware
    assert resp.status_code == 401
    assert "API key" not in resp.json().get("detail", "")


def test_bearer_token_accepted(client, monkeypatch):
    monkeypatch.setattr(security_settings, "api_key", "secret-123")
    ok = client.get("/api/mandatos", headers={"Authorization": "Bearer secret-123"})
    assert ok.status_code != 401
