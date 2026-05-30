"""Autenticación de usuario (Clerk) + verificación de cuenta empresarial.

- `is_business_email()` / `assert_business_account()`: regla "solo empresas"
  (rechaza dominios de consumo; exige Workspace `hd` en Google y cuenta
  work/school en Microsoft). Implementado y testeado — núcleo del requerimiento.
- `get_current_principal`: dependencia FastAPI. Si Clerk no está configurado
  (`settings.clerk_enabled` False), queda INERTE (devuelve None) para no romper
  el MVP. Cuando se configuren las claves, valida el JWT de sesión de Clerk.

La verificación criptográfica del JWT (JWKS RS256) se enchufa en P2 cuando
existan las claves de Clerk; aquí queda la estructura y el fail-closed.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from app.core.config import settings

# Dominio de Microsoft para cuentas personales (MSA): si el tenant es este,
# NO es una cuenta de empresa.
MS_PERSONAL_TENANT = "9188040d-6c67-4c5b-b112-36a304b66dad"


@dataclass
class Principal:
    clerk_user_id: str | None
    clerk_org_id: str | None
    email: str
    org_db_id: int | None = None


def _domain_of(email: str) -> str | None:
    email = (email or "").strip().lower()
    if "@" not in email:
        return None
    domain = email.rsplit("@", 1)[1]
    return domain or None


def is_business_email(email: str) -> tuple[bool, str | None]:
    """(True, None) si parece cuenta empresarial; (False, motivo) si no."""
    domain = _domain_of(email)
    if domain is None:
        return False, "email_invalido"
    if domain in settings.consumer_email_domains_set:
        return False, "dominio_de_consumo"
    # Heurística extra: subdominios de proveedores de consumo (ej. mail.gmail.com)
    if any(domain.endswith("." + d) for d in settings.consumer_email_domains_set):
        return False, "dominio_de_consumo"
    return True, None


def assert_business_account(
    email: str,
    *,
    provider: str | None = None,
    google_hd: str | None = None,
    ms_tenant_id: str | None = None,
) -> tuple[bool, str | None]:
    """Verificación reforzada según el proveedor del SSO.

    - google: exige claim `hd` (Google Workspace). Sin `hd` = cuenta personal.
    - microsoft: rechaza el tenant de cuentas personales (MSA).
    - email/password u otros: sólo la regla de dominio de consumo.
    """
    ok, reason = is_business_email(email)
    if not ok:
        return ok, reason
    if provider == "google" and not (google_hd and google_hd.strip()):
        return False, "google_sin_workspace"
    if provider == "microsoft" and ms_tenant_id == MS_PERSONAL_TENANT:
        return False, "microsoft_cuenta_personal"
    return True, None


def _bearer(request: Request) -> str | None:
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


def verify_session_token(token: str) -> Principal:
    """Verifica el JWT de sesión de Clerk (RS256 vía JWKS).

    P2: enchufar PyJWT + PyJWKClient con settings.clerk_jwks_url / issuer.
    Hasta entonces, fail-closed si alguien intenta autenticar con Clerk activo.
    """
    raise NotImplementedError(
        "Verificación JWT de Clerk pendiente (P2): configurar JWKS + PyJWT."
    )


def get_current_principal(request: Request) -> Principal | None:
    """Dependencia FastAPI. None si Clerk está desactivado (MVP)."""
    if not settings.clerk_enabled:
        return None
    token = _bearer(request)
    if not token:
        return None
    return verify_session_token(token)
