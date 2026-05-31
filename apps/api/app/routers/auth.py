"""Rutas de autenticación self-hosted (email + password). El SSO Google/Microsoft
se agrega en routers/auth_oauth.py cuando estén las credenciales OAuth.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import AuthError, Principal, require_principal, sign_session_jwt
from app.db.session import get_db
from app.models.organization import Organization, User
from app.schemas.auth import AuthResponse, LoginPayload, RegisterPayload, UserRead
from app.services.auth_service import AuthService

router = APIRouter(tags=["auth"])

_ERROR_STATUS = {
    "dominio_de_consumo": 422,
    "email_invalido": 422,
    "google_sin_workspace": 422,
    "microsoft_cuenta_personal": 422,
    "cuenta_no_empresarial": 422,
    "email_ya_registrado": 409,
    "credenciales_invalidas": 401,
}

_ERROR_MESSAGE = {
    "dominio_de_consumo": "Usá un correo corporativo (no gmail/outlook/etc.).",
    "email_invalido": "El email no es válido.",
    "google_sin_workspace": "La cuenta de Google debe ser de Google Workspace (empresa).",
    "microsoft_cuenta_personal": "La cuenta de Microsoft debe ser corporativa (no personal).",
    "cuenta_no_empresarial": "Solo se permiten cuentas de empresa.",
    "email_ya_registrado": "Ya existe una cuenta con ese email.",
    "credenciales_invalidas": "Email o contraseña incorrectos.",
}


def _auth_response(db: Session, user: User) -> dict:
    org = db.get(Organization, user.organization_id) if user.organization_id else None
    token = sign_session_jwt(
        user_id=user.id, email=user.email, org_db_id=user.organization_id, role=user.role
    )
    return {"token": token, "user": user, "organization": org}


def _raise(error: AuthError) -> None:
    status = _ERROR_STATUS.get(error.reason, 400)
    raise HTTPException(status_code=status, detail=_ERROR_MESSAGE.get(error.reason, error.reason))


@router.post("/api/auth/register", response_model=AuthResponse, status_code=201)
def register(payload: RegisterPayload, db: Session = Depends(get_db)) -> dict:
    service = AuthService(db)
    try:
        user = service.register(
            email=payload.email, password=payload.password, full_name=payload.full_name
        )
    except AuthError as error:
        _raise(error)
    return _auth_response(db, user)


@router.post("/api/auth/login", response_model=AuthResponse)
def login(payload: LoginPayload, db: Session = Depends(get_db)) -> dict:
    service = AuthService(db)
    try:
        user = service.authenticate(email=payload.email, password=payload.password)
    except AuthError as error:
        _raise(error)
    return _auth_response(db, user)


@router.get("/api/auth/me", response_model=UserRead)
def me(
    principal: Principal = Depends(require_principal), db: Session = Depends(get_db)
) -> User:
    user = db.get(User, principal.user_id) if principal.user_id else None
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user
