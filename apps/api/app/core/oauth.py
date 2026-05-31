"""SSO OAuth (Google / Microsoft) — authorization-code flow, self-hosted.

- `build_authorize_url`: arma la URL del proveedor con `state` firmado (anti-CSRF).
- `exchange_code`: intercambia el code por tokens (httpx; aislado para test).
- `extract_claims`: decodifica el id_token y normaliza email/sub/hd/tid/name.

La validación 'solo empresa' (Google Workspace `hd`, Microsoft tenant work/school)
se hace en el router con `assert_business_account`.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from urllib.parse import urlencode

from app.core.config import settings


class OAuthError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


_STATE_TTL = 600  # 10 min


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64url_decode(segment: str) -> bytes:
    pad = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + pad)


# --- State firmado (anti-CSRF), sin estado de servidor ----------------------


def sign_state(provider: str) -> str:
    body = _b64url_encode(
        json.dumps({"p": provider, "n": os.urandom(8).hex(), "exp": int(time.time()) + _STATE_TTL}).encode()
    )
    sig = _b64url_encode(hmac.new(settings.auth_jwt_secret.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def verify_state(state: str, provider: str) -> None:
    try:
        body, sig = state.split(".")
    except ValueError as exc:
        raise OAuthError("state_malformado") from exc
    expected = _b64url_encode(hmac.new(settings.auth_jwt_secret.encode(), body.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(expected, sig):
        raise OAuthError("state_invalido")
    data = json.loads(_b64url_decode(body))
    if data.get("p") != provider:
        raise OAuthError("state_proveedor")
    if time.time() > float(data.get("exp", 0)):
        raise OAuthError("state_expirado")


# --- Config por proveedor ---------------------------------------------------


def _provider_conf(provider: str) -> dict:
    if provider == "google":
        if not settings.google_oauth_enabled:
            raise OAuthError("proveedor_no_configurado")
        return {
            "authorize": "https://accounts.google.com/o/oauth2/v2/auth",
            "token": "https://oauth2.googleapis.com/token",
            "scope": "openid email profile",
            "client_id": settings.google_oauth_client_id,
            "client_secret": settings.google_oauth_client_secret,
            "extra_auth": {"access_type": "online", "prompt": "select_account"},
        }
    if provider == "microsoft":
        if not settings.microsoft_oauth_enabled:
            raise OAuthError("proveedor_no_configurado")
        tenant = settings.microsoft_oauth_tenant or "organizations"
        base = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0"
        return {
            "authorize": f"{base}/authorize",
            "token": f"{base}/token",
            "scope": "openid email profile User.Read",
            "client_id": settings.microsoft_oauth_client_id,
            "client_secret": settings.microsoft_oauth_client_secret,
            "extra_auth": {"prompt": "select_account"},
        }
    raise OAuthError("proveedor_desconocido")


def redirect_uri(provider: str) -> str:
    return f"{settings.oauth_redirect_base}/api/auth/oauth/{provider}/callback"


def build_authorize_url(provider: str) -> str:
    conf = _provider_conf(provider)
    params = {
        "client_id": conf["client_id"],
        "redirect_uri": redirect_uri(provider),
        "response_type": "code",
        "scope": conf["scope"],
        "state": sign_state(provider),
        **conf.get("extra_auth", {}),
    }
    return f"{conf['authorize']}?{urlencode(params)}"


def exchange_code(provider: str, code: str) -> dict:
    """Intercambia el authorization code por tokens. Aislado para poder mockear."""
    import httpx  # import diferido (solo en runtime real)

    conf = _provider_conf(provider)
    data = {
        "client_id": conf["client_id"],
        "client_secret": conf["client_secret"],
        "code": code,
        "redirect_uri": redirect_uri(provider),
        "grant_type": "authorization_code",
    }
    resp = httpx.post(conf["token"], data=data, timeout=20.0)
    if resp.status_code != 200:
        raise OAuthError("intercambio_fallido")
    return resp.json()


def extract_claims(provider: str, token_response: dict) -> dict:
    """Decodifica el payload del id_token (canal TLS server-to-server) y normaliza.

    Nota: no se verifica la firma del id_token aquí; llega por la llamada TLS
    directa al token endpoint del proveedor. Endurecer con verificación JWKS
    (RS256) es un hardening posterior.
    """
    id_token = token_response.get("id_token")
    if not id_token or id_token.count(".") != 2:
        raise OAuthError("id_token_ausente")
    try:
        payload = json.loads(_b64url_decode(id_token.split(".")[1]))
    except (ValueError, json.JSONDecodeError) as exc:
        raise OAuthError("id_token_invalido") from exc

    email = (payload.get("email") or payload.get("preferred_username") or "").strip().lower()
    return {
        "email": email,
        "subject": payload.get("sub") or payload.get("oid") or "",
        "name": payload.get("name"),
        "google_hd": payload.get("hd"),
        "ms_tenant_id": payload.get("tid"),
    }
