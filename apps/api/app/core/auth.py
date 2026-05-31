"""Autenticación de usuario (Supabase Auth) + verificación de cuenta empresarial.

- `is_business_email()` / `assert_business_account()`: regla "solo empresas"
  (rechaza dominios de consumo; exige Workspace `hd` en Google y cuenta
  work/school en Microsoft). Núcleo del requerimiento.
- `verify_supabase_jwt()`: verifica el JWT de sesión de Supabase (HS256 con el
  JWT secret del proyecto) sin dependencias externas (stdlib hmac/base64).
- `get_current_principal`: dependencia FastAPI. Si Supabase no está configurado
  (`settings.supabase_enabled` False), queda INERTE (devuelve None) para no
  romper el MVP. Con secret configurado, exige y valida el Bearer token.

Self-service: cualquier empresa se registra (SSO Google/Microsoft o
email+password) vía Supabase; el backend valida el token y aplica la regla
business-only. Las organizaciones las modelamos nosotros (tablas locales).
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import time
from dataclasses import dataclass

from fastapi import HTTPException, Request

from app.core.config import settings

MS_PERSONAL_TENANT = "9188040d-6c67-4c5b-b112-36a304b66dad"


class AuthError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass
class Principal:
    auth_user_id: str | None
    email: str
    org_db_id: int | None = None


# --- Verificación cuenta empresarial ---------------------------------------


def _domain_of(email: str) -> str | None:
    email = (email or "").strip().lower()
    if "@" not in email:
        return None
    domain = email.rsplit("@", 1)[1]
    return domain or None


def is_business_email(email: str) -> tuple[bool, str | None]:
    domain = _domain_of(email)
    if domain is None:
        return False, "email_invalido"
    consumer = settings.consumer_email_domains_set
    if domain in consumer:
        return False, "dominio_de_consumo"
    if any(domain.endswith("." + d) for d in consumer):
        return False, "dominio_de_consumo"
    return True, None


def assert_business_account(
    email: str,
    *,
    provider: str | None = None,
    google_hd: str | None = None,
    ms_tenant_id: str | None = None,
) -> tuple[bool, str | None]:
    ok, reason = is_business_email(email)
    if not ok:
        return ok, reason
    if provider == "google" and not (google_hd and google_hd.strip()):
        return False, "google_sin_workspace"
    if provider == "microsoft" and ms_tenant_id == MS_PERSONAL_TENANT:
        return False, "microsoft_cuenta_personal"
    return True, None


# --- Verificación JWT Supabase (HS256, stdlib) -----------------------------


def _b64url_decode(segment: str) -> bytes:
    pad = "=" * (-len(segment) % 4)
    try:
        return base64.urlsafe_b64decode(segment + pad)
    except (binascii.Error, ValueError) as exc:
        raise AuthError("token_malformado") from exc


def verify_supabase_jwt(token: str, *, secret: str | None = None, audience: str | None = None) -> dict:
    """Valida firma HS256, expiración y audiencia. Devuelve el payload."""
    secret = secret if secret is not None else settings.supabase_jwt_secret
    audience = audience if audience is not None else settings.supabase_jwt_audience
    if not secret:
        raise AuthError("auth_no_configurada")
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthError("token_malformado")
    header_b64, payload_b64, sig_b64 = parts
    try:
        header = json.loads(_b64url_decode(header_b64))
    except (json.JSONDecodeError, ValueError) as exc:
        raise AuthError("token_malformado") from exc
    if header.get("alg") != "HS256":
        raise AuthError("alg_no_soportado")
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _b64url_decode(sig_b64)):
        raise AuthError("firma_invalida")
    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except (json.JSONDecodeError, ValueError) as exc:
        raise AuthError("token_malformado") from exc
    exp = payload.get("exp")
    if exp is not None and time.time() > float(exp):
        raise AuthError("token_expirado")
    if audience and payload.get("aud") and payload.get("aud") != audience:
        raise AuthError("audiencia_invalida")
    return payload


def principal_from_payload(payload: dict) -> Principal:
    return Principal(
        auth_user_id=payload.get("sub"),
        email=(payload.get("email") or "").strip().lower(),
    )


# --- Dependencias FastAPI ---------------------------------------------------


def _bearer(request: Request) -> str | None:
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


def get_current_principal(request: Request) -> Principal | None:
    """None si Supabase está desactivado (MVP). Si no, exige token válido."""
    if not settings.supabase_enabled:
        return None
    token = _bearer(request)
    if not token:
        raise HTTPException(status_code=401, detail="Falta el token de sesión.")
    try:
        payload = verify_supabase_jwt(token)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=f"Token inválido: {exc.reason}") from exc
    return principal_from_payload(payload)
