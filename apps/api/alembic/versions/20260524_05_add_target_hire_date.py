"""add target hire date to search mandates

Revision ID: 20260524_05
Revises: 20260523_04
Create Date: 2026-05-24
"""

from alembic import op
import sqlalchemy as sa


revision = "20260524_05"
down_revision = "20260523_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "search_mandates",
        sa.Column("target_hire_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("search_mandates", "target_hire_date")
