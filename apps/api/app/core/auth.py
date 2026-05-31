"""Autenticación self-hosted (en Fly, sobre el Postgres propio).

- `is_business_email()` / `assert_business_account()`: regla "solo empresas".
- `hash_password()` / `verify_password()`: scrypt de stdlib (sin dependencias).
- `sign_session_jwt()` / `verify_session_jwt()`: emitimos y verificamos nuestros
  propios JWT de sesión (HS256 con `auth_jwt_secret`).
- `get_current_principal` / `require_principal`: dependencias FastAPI.

Email+password está 100% acá. El SSO (Google/Microsoft) usa estas mismas
piezas (assert_business_account + sign_session_jwt) desde el router de OAuth.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass

from fastapi import HTTPException, Request

from app.core.config import settings

MS_PERSONAL_TENANT = "9188040d-6c67-4c5b-b112-36a304b66dad"
_SCRYPT_N = 16384
_SCRYPT_R = 8
_SCRYPT_P = 1


class AuthError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass
class Principal:
    user_id: int | None
    email: str
    org_db_id: int | None = None
    role: str = "member"


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


# --- Password hashing (scrypt, stdlib) -------------------------------------


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=32
    )
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        algo, n, r, p, salt_hex, hash_hex = stored.split("$")
        if algo != "scrypt":
            return False
        dk = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(bytes.fromhex(hash_hex)),
        )
        return hmac.compare_digest(dk, bytes.fromhex(hash_hex))
    except (ValueError, TypeError):
        return False


# --- JWT (HS256, stdlib) — emitido y verificado por nosotros ---------------


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64url_decode(segment: str) -> bytes:
    pad = "=" * (-len(segment) % 4)
    try:
        return base64.urlsafe_b64decode(segment + pad)
    except (binascii.Error, ValueError) as exc:
        raise AuthError("token_malformado") from exc


def sign_session_jwt(
    *, user_id: int, email: str, org_db_id: int | None, role: str = "member", ttl: int | None = None
) -> str:
    ttl = ttl if ttl is not None else settings.auth_jwt_ttl_seconds
    now = int(time.time())
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url_encode(
        json.dumps(
            {
                "sub": str(user_id),
                "email": email,
                "org": org_db_id,
                "role": role,
                "aud": settings.auth_jwt_audience,
                "iat": now,
                "exp": now + ttl,
            }
        ).encode()
    )
    signing_input = f"{header}.{payload}".encode()
    sig = _b64url_encode(
        hmac.new(settings.auth_jwt_secret.encode(), signing_input, hashlib.sha256).digest()
    )
    return f"{header}.{payload}.{sig}"


def verify_session_jwt(token: str) -> dict:
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
    expected = hmac.new(settings.auth_jwt_secret.encode(), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _b64url_decode(sig_b64)):
        raise AuthError("firma_invalida")
    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except (json.JSONDecodeError, ValueError) as exc:
        raise AuthError("token_malformado") from exc
    if payload.get("exp") is not None and time.time() > float(payload["exp"]):
        raise AuthError("token_expirado")
    if payload.get("aud") != settings.auth_jwt_audience:
        raise AuthError("audiencia_invalida")
    return payload


def principal_from_payload(payload: dict) -> Principal:
    sub = payload.get("sub")
    return Principal(
        user_id=int(sub) if sub is not None and str(sub).isdigit() else None,
        email=(payload.get("email") or "").strip().lower(),
        org_db_id=payload.get("org"),
        role=payload.get("role") or "member",
    )


# --- Dependencias FastAPI ---------------------------------------------------


def _bearer(request: Request) -> str | None:
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


def get_current_principal(request: Request) -> Principal | None:
    """Principal del token si viene; None si no hay token. 401 si el token es inválido."""
    token = _bearer(request)
    if not token:
        return None
    try:
        return principal_from_payload(verify_session_jwt(token))
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=f"Token inválido: {exc.reason}") from exc


def require_principal(request: Request) -> Principal:
    """Para rutas protegidas: exige sesión válida (usar en el cutover P5)."""
    principal = get_current_principal(request)
    if principal is None:
        raise HTTPException(status_code=401, detail="Autenticación requerida.")
    return principal
