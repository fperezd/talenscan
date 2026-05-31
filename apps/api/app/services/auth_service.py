"""Servicio de autenticación self-hosted: registro, login y SSO upsert.

Modela organizaciones por dominio de email (cada empresa = una org). Aplica la
regla 'solo cuentas empresariales' en el alta.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import (
    AuthError,
    assert_business_account,
    hash_password,
    verify_password,
)
from app.models.organization import Organization, User


def _domain(email: str) -> str:
    return email.strip().lower().rsplit("@", 1)[1]


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.scalars(
            select(User).where(func.lower(User.email) == email.strip().lower())
        ).first()

    def get_or_create_org_for_domain(self, domain: str) -> Organization:
        org = self.db.scalars(
            select(Organization).where(func.lower(Organization.primary_domain) == domain.lower())
        ).first()
        if org is not None:
            return org
        org = Organization(name=domain, primary_domain=domain, plan="free")
        self.db.add(org)
        self.db.flush()
        return org

    def register(
        self,
        *,
        email: str,
        password: str,
        full_name: str | None,
        provider: str | None = None,
        google_hd: str | None = None,
        ms_tenant_id: str | None = None,
    ) -> User:
        email = email.strip().lower()
        ok, reason = assert_business_account(
            email, provider=provider, google_hd=google_hd, ms_tenant_id=ms_tenant_id
        )
        if not ok:
            raise AuthError(reason or "cuenta_no_empresarial")
        if self.get_user_by_email(email) is not None:
            raise AuthError("email_ya_registrado")

        org = self.get_or_create_org_for_domain(_domain(email))
        # El primer usuario de una organización es 'owner'.
        is_first = (
            self.db.scalars(
                select(func.count(User.id)).where(User.organization_id == org.id)
            ).one()
            == 0
        )
        user = User(
            email=email,
            full_name=full_name,
            organization_id=org.id,
            role="owner" if is_first else "member",
            password_hash=hash_password(password) if password else None,
            email_verified=False,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, *, email: str, password: str) -> User:
        user = self.get_user_by_email(email)
        if user is None or not user.is_active:
            raise AuthError("credenciales_invalidas")
        if not verify_password(password, user.password_hash):
            raise AuthError("credenciales_invalidas")
        return user

    def upsert_oauth_user(
        self,
        *,
        email: str,
        provider: str,
        subject: str,
        full_name: str | None,
        google_hd: str | None = None,
        ms_tenant_id: str | None = None,
    ) -> User:
        """Crea o vincula un usuario que entra por SSO (Google/Microsoft)."""
        email = email.strip().lower()
        ok, reason = assert_business_account(
            email, provider=provider, google_hd=google_hd, ms_tenant_id=ms_tenant_id
        )
        if not ok:
            raise AuthError(reason or "cuenta_no_empresarial")
        user = self.get_user_by_email(email)
        if user is None:
            org = self.get_or_create_org_for_domain(_domain(email))
            is_first = (
                self.db.scalars(
                    select(func.count(User.id)).where(User.organization_id == org.id)
                ).one()
                == 0
            )
            user = User(
                email=email,
                full_name=full_name,
                organization_id=org.id,
                role="owner" if is_first else "member",
                oauth_provider=provider,
                oauth_subject=subject,
                email_verified=True,  # el proveedor ya verificó el email
            )
            self.db.add(user)
        else:
            user.oauth_provider = provider
            user.oauth_subject = subject
            user.email_verified = True
            if full_name and not user.full_name:
                user.full_name = full_name
            self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
