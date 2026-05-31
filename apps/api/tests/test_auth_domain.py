"""Tests de la regla 'solo empresa', hashing de password y JWT propio."""

from __future__ import annotations

import time

import pytest
from starlette.requests import Request

from app.core.auth import (
    MS_PERSONAL_TENANT,
    AuthError,
    assert_business_account,
    get_current_principal,
    hash_password,
    is_business_email,
    principal_from_payload,
    sign_session_jwt,
    verify_password,
    verify_session_jwt,
)


@pytest.mark.parametrize(
    "email",
    ["juan@gmail.com", "ana@outlook.com", "x@hotmail.com", "y@yahoo.com", "z@icloud.com"],
)
def test_consumer_domains_rejected(email):
    ok, reason = is_business_email(email)
    assert ok is False and reason == "dominio_de_consumo"


@pytest.mark.parametrize("email", ["fperez@tooxs.com", "ceo@elyon.cl", "rrhh@falabella.com"])
def test_business_domains_accepted(email):
    ok, reason = is_business_email(email)
    assert ok is True and reason is None


def test_invalid_email():
    assert is_business_email("sin-arroba")[0] is False
    assert is_business_email("")[1] == "email_invalido"


def test_subdomain_of_consumer_rejected():
    assert is_business_email("user@mail.gmail.com")[0] is False


def test_google_requires_workspace_hd():
    assert assert_business_account("u@tooxs.com", provider="google", google_hd=None)[1] == "google_sin_workspace"
    assert assert_business_account("u@tooxs.com", provider="google", google_hd="tooxs.com")[0] is True


def test_microsoft_personal_tenant_rejected():
    assert (
        assert_business_account("u@tooxs.com", provider="microsoft", ms_tenant_id=MS_PERSONAL_TENANT)[1]
        == "microsoft_cuenta_personal"
    )
    assert assert_business_account("u@tooxs.com", provider="microsoft", ms_tenant_id="contoso")[0] is True


# --- Password hashing ------------------------------------------------------


def test_password_hash_roundtrip():
    h = hash_password("Sup3rSecret!")
    assert h.startswith("scrypt$")
    assert verify_password("Sup3rSecret!", h) is True
    assert verify_password("otra", h) is False
    assert verify_password("x", None) is False


def test_password_hash_is_salted():
    assert hash_password("misma") != hash_password("misma")


# --- JWT propio ------------------------------------------------------------


def test_jwt_roundtrip():
    token = sign_session_jwt(user_id=7, email="ANA@tooxs.com", org_db_id=3, role="owner")
    payload = verify_session_jwt(token)
    p = principal_from_payload(payload)
    assert p.user_id == 7 and p.org_db_id == 3 and p.role == "owner"


def test_jwt_tampered_rejected():
    token = sign_session_jwt(user_id=1, email="a@b.com", org_db_id=None)
    tampered = token[:-3] + ("aaa" if not token.endswith("aaa") else "bbb")
    with pytest.raises(AuthError):
        verify_session_jwt(tampered)


def test_jwt_expired_rejected():
    token = sign_session_jwt(user_id=1, email="a@b.com", org_db_id=None, ttl=-10)
    try:
        verify_session_jwt(token)
        assert False, "debería expirar"
    except AuthError as exc:
        assert exc.reason == "token_expirado"


def _req(headers=None):
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    return Request({"type": "http", "method": "GET", "path": "/api/x", "headers": raw})


def test_principal_none_without_token():
    assert get_current_principal(_req()) is None


def test_principal_from_valid_bearer():
    token = sign_session_jwt(user_id=42, email="x@empresa.com", org_db_id=1)
    p = get_current_principal(_req({"authorization": f"Bearer {token}"}))
    assert p is not None and p.user_id == 42
