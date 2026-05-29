"""expand search mandates fields

Revision ID: 20260523_02
Revises: 20260523_01
Create Date: 2026-05-23
"""

from alembic import op
import sqlalchemy as sa


revision = "20260523_02"
down_revision = "20260523_01"
branch_labels = None
depends_on = None


json_empty = sa.text("'[]'::json")


def upgrade() -> None:
    op.add_column("search_mandates", sa.Column("industry", sa.String(length=150), nullable=True))
    op.add_column("search_mandates", sa.Column("work_mode", sa.String(length=60), nullable=True))
    op.add_column("search_mandates", sa.Column("seniority_level", sa.String(length=80), nullable=True))
    op.add_column("search_mandates", sa.Column("reports_to", sa.String(length=150), nullable=True))
    op.add_column("search_mandates", sa.Column("key_challenges", sa.Text(), nullable=True))
    op.add_column(
        "search_mandates",
        sa.Column("main_responsibilities", sa.JSON(), nullable=False, server_default=json_empty),
    )
    op.add_column("search_mandates", sa.Column("expected_results", sa.JSON(), nullable=False, server_default=json_empty))
    op.add_column(
        "search_mandates",
        sa.Column("must_have_requirements", sa.JSON(), nullable=False, server_default=json_empty),
    )
    op.add_column(
        "search_mandates",
        sa.Column("nice_to_have_requirements", sa.JSON(), nullable=False, server_default=json_empty),
    )
    op.add_column("search_mandates", sa.Column("target_companies", sa.JSON(), nullable=False, server_default=json_empty))
    op.add_column("search_mandates", sa.Column("target_industries", sa.JSON(), nullable=False, server_default=json_empty))
    op.add_column("search_mandates", sa.Column("equivalent_roles", sa.JSON(), nullable=False, server_default=json_empty))
    op.add_column("search_mandates", sa.Column("compensation_context", sa.Text(), nullable=True))
    op.add_column("search_mandates", sa.Column("urgency", sa.String(length=60), nullable=True))
    op.add_column("search_mandates", sa.Column("comments", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("search_mandates", "comments")
    op.drop_column("search_mandates", "urgency")
    op.drop_column("search_mandates", "compensation_context")
    op.drop_column("search_mandates", "equivalent_roles")
    op.drop_column("search_mandates", "target_industries")
    op.drop_column("search_mandates", "target_companies")
    op.drop_column("search_mandates", "nice_to_have_requirements")
    op.drop_column("search_mandates", "must_have_requirements")
    op.drop_column("search_mandates", "expected_results")
    op.drop_column("search_mandates", "main_responsibilities")
    op.drop_column("search_mandates", "key_challenges")
    op.drop_column("search_mandates", "reports_to")
    op.drop_column("search_mandates", "seniority_level")
    op.drop_column("search_mandates", "work_mode")
    op.drop_column("search_mandates", "industry")
