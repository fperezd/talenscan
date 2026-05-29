"""create client_shortlists and client_shortlist_items

Revision ID: 20260527_07
Revises: 20260525_06
Create Date: 2026-05-27
"""

from alembic import op
import sqlalchemy as sa


revision = "20260527_07"
down_revision = "20260525_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_shortlists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mandate_id", sa.Integer(), sa.ForeignKey("search_mandates.id"), nullable=False),
        sa.Column("public_token", sa.String(length=64), nullable=False, unique=True),
        sa.Column("title", sa.String(length=200), nullable=False, server_default="Shortlist Talenscan"),
        sa.Column("message_to_client", sa.Text(), nullable=False, server_default=""),
        sa.Column("show_scores", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("viewed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_client_shortlists_mandate_id", "client_shortlists", ["mandate_id"])
    op.create_index("ix_client_shortlists_public_token", "client_shortlists", ["public_token"], unique=True)

    op.create_table(
        "client_shortlist_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shortlist_id", sa.Integer(), sa.ForeignKey("client_shortlists.id"), nullable=False),
        sa.Column("evaluation_id", sa.Integer(), sa.ForeignKey("candidate_evaluations.id"), nullable=True),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("client_status", sa.String(length=40), nullable=True),
        sa.Column("client_comment", sa.Text(), nullable=True),
        sa.Column("status_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_client_shortlist_items_shortlist_id", "client_shortlist_items", ["shortlist_id"])
    op.create_index("ix_client_shortlist_items_candidate_id", "client_shortlist_items", ["candidate_id"])


def downgrade() -> None:
    op.drop_index("ix_client_shortlist_items_candidate_id", table_name="client_shortlist_items")
    op.drop_index("ix_client_shortlist_items_shortlist_id", table_name="client_shortlist_items")
    op.drop_table("client_shortlist_items")
    op.drop_index("ix_client_shortlists_public_token", table_name="client_shortlists")
    op.drop_index("ix_client_shortlists_mandate_id", table_name="client_shortlists")
    op.drop_table("client_shortlists")
