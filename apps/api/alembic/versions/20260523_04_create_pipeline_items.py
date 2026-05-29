"""create candidate pipeline items

Revision ID: 20260523_04
Revises: 20260523_03
Create Date: 2026-05-23
"""

from alembic import op
import sqlalchemy as sa


revision = "20260523_04"
down_revision = "20260523_03"
branch_labels = None
depends_on = None


json_empty_list = sa.text("'[]'::json")


def upgrade() -> None:
    op.create_table(
        "candidate_pipeline_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mandate_id", sa.Integer(), sa.ForeignKey("search_mandates.id"), nullable=False),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column(
            "evaluation_id",
            sa.Integer(),
            sa.ForeignKey("candidate_evaluations.id"),
            nullable=True,
        ),
        sa.Column("stage", sa.String(length=40), nullable=False, server_default="received"),
        sa.Column("stage_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_priority", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_shortlisted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("consultant_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("discard_reason", sa.String(length=240), nullable=False, server_default=""),
        sa.Column("tags", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("last_moved_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("mandate_id", "candidate_id", name="uq_pipeline_mandate_candidate"),
    )
    op.create_index(
        "ix_candidate_pipeline_items_mandate_id", "candidate_pipeline_items", ["mandate_id"]
    )
    op.create_index(
        "ix_candidate_pipeline_items_candidate_id", "candidate_pipeline_items", ["candidate_id"]
    )
    op.create_index(
        "ix_candidate_pipeline_items_evaluation_id", "candidate_pipeline_items", ["evaluation_id"]
    )
    op.create_index("ix_candidate_pipeline_items_stage", "candidate_pipeline_items", ["stage"])


def downgrade() -> None:
    op.drop_index("ix_candidate_pipeline_items_stage", table_name="candidate_pipeline_items")
    op.drop_index("ix_candidate_pipeline_items_evaluation_id", table_name="candidate_pipeline_items")
    op.drop_index("ix_candidate_pipeline_items_candidate_id", table_name="candidate_pipeline_items")
    op.drop_index("ix_candidate_pipeline_items_mandate_id", table_name="candidate_pipeline_items")
    op.drop_table("candidate_pipeline_items")
