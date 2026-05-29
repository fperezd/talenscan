"""make candidate_profile.candidate_document_id nullable for linkedin-only profiles

Revision ID: 20260525_06
Revises: 20260524_05
Create Date: 2026-05-25
"""

from alembic import op
import sqlalchemy as sa


revision = "20260525_06"
down_revision = "20260524_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "candidate_profiles",
        "candidate_document_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "candidate_profiles",
        "candidate_document_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
