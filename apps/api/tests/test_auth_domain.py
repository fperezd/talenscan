"""Tests de la verificación 'solo cuentas empresariales' y del gating de auth."""

from __future__ import annotations

import pytest
from starlette.requests import Request

from app.core.auth import (
    MS_PERSONAL_TENANT,
    assert_business_account,
    get_current_principal,
    is_business_email,
)
from app.core.config import settings


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


def test_principal_none_when_clerk_disabled(monkeypatch):
    monkeypatch.setattr(settings, "clerk_secret_key", "")
    monkeypatch.setattr(settings, "clerk_jwks_url", "")
    assert get_current_principal(_req()) is None
