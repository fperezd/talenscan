"""create organizations and users (auth multi-tenant foundation)

Revision ID: 20260530_11
Revises: 20260530_10
Create Date: 2026-05-30
"""

from alembic import op
import sqlalchemy as sa


revision = "20260530_11"
down_revision = "20260530_10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("clerk_org_id", sa.String(length=80), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("primary_domain", sa.String(length=200), nullable=True),
        sa.Column("plan", sa.String(length=40), nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("clerk_org_id", name="uq_org_clerk_id"),
    )
    op.create_index("ix_organizations_clerk_org_id", "organizations", ["clerk_org_id"])
    op.create_index("ix_organizations_primary_domain", "organizations", ["primary_domain"])

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("clerk_user_id", sa.String(length=80), nullable=True),
        sa.Column(
            "organization_id",
            sa.BigInteger(),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("email", sa.String(length=200), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="member"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("clerk_user_id", name="uq_user_clerk_id"),
    )
    op.create_index("ix_users_clerk_user_id", "users", ["clerk_user_id"])
    op.create_index("ix_users_organization_id", "users", ["organization_id"])
    op.create_index("ix_users_email", "users", ["email"])


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_organization_id", table_name="users")
    op.drop_index("ix_users_clerk_user_id", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_organizations_primary_domain", table_name="organizations")
    op.drop_index("ix_organizations_clerk_org_id", table_name="organizations")
    op.drop_table("organizations")
