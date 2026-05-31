"""Tests de la verificación 'solo cuentas empresariales' y del gating de auth."""

from __future__ import annotations

import pytest
from starlette.requests import Request

import base64
import hashlib
import hmac
import json
import time

from app.core.auth import (
    MS_PERSONAL_TENANT,
    AuthError,
    assert_business_account,
    get_current_principal,
    is_business_email,
    principal_from_payload,
    verify_supabase_jwt,
)
from app.core.config import settings


def _mint_hs256(payload: dict, secret: str) -> str:
    def b64(raw: bytes) -> str:
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = b64(json.dumps(payload).encode())
    signing_input = f"{header}.{body}".encode()
    sig = b64(hmac.new(secret.encode(), signing_input, hashlib.sha256).digest())
    return f"{header}.{body}.{sig}"


@pytest.mark.parametrize(
    "email",
    ["juan@gmail.com", "ana@outlook.com", "x@hotmail.com", "y@yahoo.com", "z@icloud.com"],
)
def test_consumer_domains_rejected(email):
    ok, reason = is_business_email(email)
    assert ok is False
    assert reason == "dominio_de_consumo"


@pytest.mark.parametrize("email", ["fperez@tooxs.com", "ceo@elyon.cl", "rrhh@falabella.com"])
def test_business_domains_accepted(email):
    ok, reason = is_business_email(email)
    assert ok is True
    assert reason is None


def test_invalid_email():
    assert is_business_email("sin-arroba")[0] is False
    assert is_business_email("")[1] == "email_invalido"


def test_subdomain_of_consumer_rejected():
    assert is_business_email("user@mail.gmail.com")[0] is False


def test_google_requires_workspace_hd():
    # Google sin hd → personal, rechazado
    ok, reason = assert_business_account("user@tooxs.com", provider="google", google_hd=None)
    assert ok is False and reason == "google_sin_workspace"
    # Google con hd → ok
    ok, _ = assert_business_account("user@tooxs.com", provider="google", google_hd="tooxs.com")
    assert ok is True


def test_microsoft_personal_tenant_rejected():
    ok, reason = assert_business_account(
        "user@tooxs.com", provider="microsoft", ms_tenant_id=MS_PERSONAL_TENANT
    )
    assert ok is False and reason == "microsoft_cuenta_personal"
    # Tenant de empresa → ok
    ok, _ = assert_business_account(
        "user@tooxs.com", provider="microsoft", ms_tenant_id="contoso-tenant-guid"
    )
    assert ok is True


def test_email_password_business_only():
    # Por email/password igual aplica la regla de dominio
    assert assert_business_account("nuevo@gmail.com")[0] is False
    assert assert_business_account("nuevo@empresa.com")[0] is True


def _req() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/api/x", "headers": []})


def test_principal_none_when_supabase_disabled(monkeypatch):
    monkeypatch.setattr(settings, "supabase_jwt_secret", "")
    assert get_current_principal(_req()) is None


def test_jwt_valid_signature_and_claims():
    secret = "test-jwt-secret"
    token = _mint_hs256(
        {"sub": "user-uuid-1", "email": "ANA@tooxs.com", "aud": "authenticated", "exp": time.time() + 3600},
        secret,
    )
    payload = verify_supabase_jwt(token, secret=secret, audience="authenticated")
    principal = principal_from_payload(payload)
    assert principal.auth_user_id == "user-uuid-1"
    assert principal.email == "ana@tooxs.com"  # normalizado a minúsculas


def test_jwt_tampered_signature_rejected():
    secret = "test-jwt-secret"
    token = _mint_hs256({"sub": "u", "email": "a@b.com", "exp": time.time() + 60}, secret)
    tampered = token[:-4] + ("aaaa" if not token.endswith("aaaa") else "bbbb")
    try:
        verify_supabase_jwt(tampered, secret=secret, audience=None)
        assert False, "debería rechazar firma adulterada"
    except AuthError as exc:
        assert exc.reason in ("firma_invalida", "token_malformado")


def test_jwt_wrong_secret_rejected():
    token = _mint_hs256({"sub": "u", "email": "a@b.com", "exp": time.time() + 60}, "secret-a")
    try:
        verify_supabase_jwt(token, secret="secret-b", audience=None)
        assert False, "debería rechazar con otro secreto"
    except AuthError as exc:
        assert exc.reason == "firma_invalida"


def test_jwt_expired_rejected():
    secret = "s"
    token = _mint_hs256({"sub": "u", "email": "a@b.com", "exp": time.time() - 10}, secret)
    try:
        verify_supabase_jwt(token, secret=secret, audience=None)
        assert False, "debería rechazar token expirado"
    except AuthError as exc:
        assert exc.reason == "token_expirado"
