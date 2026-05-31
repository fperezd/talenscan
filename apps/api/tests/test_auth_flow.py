"""Tests del flujo de auth self-hosted: registro/login/me + organización por dominio."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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


def _register(client, email="fperez@tooxs.com", password="Sup3rSecret!", full_name="Fernando"):
    return client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )


def test_register_business_creates_user_and_org(client):
    resp = _register(client)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["token"]
    assert body["user"]["email"] == "fperez@tooxs.com"
    assert body["user"]["role"] == "owner"  # primero de la org
    assert body["organization"]["primary_domain"] == "tooxs.com"


def test_register_consumer_email_rejected(client):
    resp = _register(client, email="alguien@gmail.com")
    assert resp.status_code == 422
    assert "corporativo" in resp.json()["detail"].lower()


def test_register_duplicate_email(client):
    _register(client)
    resp = _register(client)
    assert resp.status_code == 409


def test_second_user_same_domain_is_member(client):
    _register(client, email="uno@empresa.com")
    resp = _register(client, email="dos@empresa.com")
    assert resp.status_code == 201
    assert resp.json()["user"]["role"] == "member"
    # misma organización
    assert resp.json()["organization"]["primary_domain"] == "empresa.com"


def test_login_ok_and_wrong_password(client):
    _register(client, email="login@empresa.com", password="Correct1!")
    ok = client.post("/api/auth/login", json={"email": "login@empresa.com", "password": "Correct1!"})
    assert ok.status_code == 200 and ok.json()["token"]
    bad = client.post("/api/auth/login", json={"email": "login@empresa.com", "password": "nope"})
    assert bad.status_code == 401


def test_me_requires_token(client):
    token = _register(client, email="me@empresa.com").json()["token"]
    assert client.get("/api/auth/me").status_code == 401
    ok = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert ok.status_code == 200
    assert ok.json()["email"] == "me@empresa.com"
