"""Tests del SSO OAuth: state firmado + flujo de callback (sin red, exchange mockeado)."""

from __future__ import annotations

import base64
import json
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import oauth as oauth_mod
from app.core.oauth import OAuthError, sign_state, verify_state
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


def _id_token(payload: dict) -> str:
    def b64(raw: bytes) -> str:
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    return f"{b64(b'{}')}.{b64(json.dumps(payload).encode())}.{b64(b'sig')}"


def _hash_fragment(location: str) -> dict:
    frag = urlparse(location).fragment
    return {k: v[0] for k, v in parse_qs(frag).items()}


# --- State -----------------------------------------------------------------


def test_state_roundtrip():
    st = sign_state("google")
    verify_state(st, "google")  # no levanta


def test_state_wrong_provider():
    st = sign_state("google")
    with pytest.raises(OAuthError):
        verify_state(st, "microsoft")


def test_state_tampered():
    st = sign_state("google")
    with pytest.raises(OAuthError):
        verify_state(st[:-2] + ("aa" if not st.endswith("aa") else "bb"), "google")


# --- start ------------------------------------------------------------------


def test_start_disabled_provider_404(client):
    # Sin credenciales configuradas → proveedor no disponible
    assert client.get("/api/auth/oauth/google/start", follow_redirects=False).status_code == 404


def test_start_unknown_provider_404(client):
    assert client.get("/api/auth/oauth/github/start", follow_redirects=False).status_code == 404


# --- callback ---------------------------------------------------------------


def test_callback_business_google_issues_token(client, monkeypatch):
    monkeypatch.setattr(
        oauth_mod, "exchange_code", lambda p, c: {"id_token": _id_token({"sub": "g1", "email": "ceo@empresa.com", "hd": "empresa.com", "name": "CEO"})}
    )
    # también el router referencia exchange_code importado: parchear ahí
    import app.routers.auth_oauth as r
    monkeypatch.setattr(r, "exchange_code", lambda p, c: {"id_token": _id_token({"sub": "g1", "email": "ceo@empresa.com", "hd": "empresa.com", "name": "CEO"})})

    state = sign_state("google")
    resp = client.get(
        f"/api/auth/oauth/google/callback?state={state}&code=abc", follow_redirects=False
    )
    assert resp.status_code == 302
    frag = _hash_fragment(resp.headers["location"])
    assert "token" in frag and frag["token"]
    # el usuario quedó creado
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {frag['token']}"})
    assert me.status_code == 200 and me.json()["email"] == "ceo@empresa.com"


def test_callback_consumer_email_redirects_error(client, monkeypatch):
    import app.routers.auth_oauth as r
    monkeypatch.setattr(r, "exchange_code", lambda p, c: {"id_token": _id_token({"sub": "g2", "email": "x@gmail.com", "hd": "gmail.com"})})
    state = sign_state("google")
    resp = client.get(f"/api/auth/oauth/google/callback?state={state}&code=abc", follow_redirects=False)
    assert resp.status_code == 302
    assert _hash_fragment(resp.headers["location"]).get("error") == "dominio_de_consumo"


def test_callback_google_without_workspace_hd(client, monkeypatch):
    import app.routers.auth_oauth as r
    monkeypatch.setattr(r, "exchange_code", lambda p, c: {"id_token": _id_token({"sub": "g3", "email": "ok@empresa.com"})})
    state = sign_state("google")
    resp = client.get(f"/api/auth/oauth/google/callback?state={state}&code=abc", follow_redirects=False)
    assert _hash_fragment(resp.headers["location"]).get("error") == "google_sin_workspace"


def test_callback_bad_state(client):
    resp = client.get("/api/auth/oauth/google/callback?state=invalido&code=abc", follow_redirects=False)
    assert resp.status_code == 302
    assert "error" in _hash_fragment(resp.headers["location"])
