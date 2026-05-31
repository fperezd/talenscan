"""Rutas SSO: /api/auth/oauth/{provider}/start y /callback (Google, Microsoft).

Flujo: start → redirige al proveedor con state firmado → el proveedor vuelve al
callback → intercambiamos el code, validamos que sea cuenta de empresa, creamos/
vinculamos el usuario y emitimos NUESTRO JWT, redirigiendo al frontend con el token
en el fragmento (#token=...).
"""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.auth import AuthError, assert_business_account, sign_session_jwt
from app.core.config import settings
from app.core.oauth import (
    OAuthError,
    build_authorize_url,
    exchange_code,
    extract_claims,
    verify_state,
)
from app.db.session import get_db
from app.services.auth_service import AuthService

router = APIRouter(tags=["auth"])

_PROVIDERS = {"google": "google", "microsoft": "microsoft"}


def _frontend_redirect(**params: str) -> RedirectResponse:
    return RedirectResponse(
        url=f"{settings.frontend_base_url}/auth/callback#{urlencode(params)}",
        status_code=302,
    )


@router.get("/api/auth/oauth/{provider}/start")
def oauth_start(provider: str) -> RedirectResponse:
    if provider not in _PROVIDERS:
        raise HTTPException(status_code=404, detail="Proveedor no soportado")
    try:
        url = build_authorize_url(provider)
    except OAuthError as exc:
        # proveedor_no_configurado → 404 para no filtrar config
        raise HTTPException(status_code=404, detail=f"SSO no disponible: {exc.reason}") from exc
    return RedirectResponse(url=url, status_code=302)


@router.get("/api/auth/oauth/{provider}/callback")
def oauth_callback(
    provider: str,
    state: str = "",
    code: str = "",
    error: str = "",
    db: Session = Depends(get_db),
) -> RedirectResponse:
    if provider not in _PROVIDERS:
        raise HTTPException(status_code=404, detail="Proveedor no soportado")
    if error:
        return _frontend_redirect(error=error)
    try:
        verify_state(state, provider)
        if not code:
            raise OAuthError("code_ausente")
        token_response = exchange_code(provider, code)
        claims = extract_claims(provider, token_response)
    except OAuthError as exc:
        return _frontend_redirect(error=exc.reason)

    ok, reason = assert_business_account(
        claims["email"],
        provider=provider,
        google_hd=claims.get("google_hd"),
        ms_tenant_id=claims.get("ms_tenant_id"),
    )
    if not ok:
        return _frontend_redirect(error=reason or "cuenta_no_empresarial")

    try:
        user = AuthService(db).upsert_oauth_user(
            email=claims["email"],
            provider=provider,
            subject=str(claims.get("subject") or ""),
            full_name=claims.get("name"),
            google_hd=claims.get("google_hd"),
            ms_tenant_id=claims.get("ms_tenant_id"),
        )
    except AuthError as exc:
        return _frontend_redirect(error=exc.reason)

    token = sign_session_jwt(
        user_id=user.id, email=user.email, org_db_id=user.organization_id, role=user.role
    )
    return _frontend_redirect(token=token)
