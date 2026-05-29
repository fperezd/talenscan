"""create search mandates table

Revision ID: 20260523_01
Revises:
Create Date: 2026-05-23
"""

from alembic import op
import sqlalchemy as sa


revision = "20260523_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "search_mandates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_name", sa.String(length=200), nullable=False),
        sa.Column("search_title", sa.String(length=200), nullable=False),
        sa.Column("target_role", sa.String(length=150), nullable=False),
        sa.Column("country", sa.String(length=120), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("business_context", sa.Text(), nullable=True),
        sa.Column("role_objective", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=60), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("search_mandates")
