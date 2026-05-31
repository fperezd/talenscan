"""Multi-tenancy: Organization (empresa) y User.

Las organizaciones las modelamos nosotros (Supabase Auth no tiene concepto de
org). `User` referencia el usuario de Supabase por `auth_user_id` (uuid de
auth.users) y pertenece a una organización. La verificación de identidad la hace
Supabase; estas tablas son la proyección local + el grafo de pertenencia.
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

_BigPk = lambda: BigInteger().with_variant(Integer, "sqlite")  # noqa: E731

USER_ROLES = ("owner", "admin", "member")


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(_BigPk(), primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    primary_domain: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    plan: Mapped[str] = mapped_column(String(40), nullable=False, default="free")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("auth_user_id", name="uq_user_auth_id"),)

    id: Mapped[int] = mapped_column(_BigPk(), primary_key=True, autoincrement=True)
    auth_user_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    email: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="member")
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
