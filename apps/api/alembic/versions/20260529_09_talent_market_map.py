"""create talent_market_map tables

Revision ID: 20260529_09
Revises: 20260527_08
Create Date: 2026-05-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "20260529_09"
down_revision = "20260527_08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- talent_market_maps -------------------------------------------------
    op.create_table(
        "talent_market_maps",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "search_mandate_id",
            sa.Integer(),
            sa.ForeignKey("search_mandates.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "position_spec_id",
            sa.Integer(),
            sa.ForeignKey("position_specs.id"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("executive_summary", sa.Text(), nullable=True),
        sa.Column("executive_summary_for_client", sa.Text(), nullable=True),
        sa.Column("market_assessment", sa.String(length=20), nullable=True),
        sa.Column("generated_by_model", sa.String(length=80), nullable=True),
        sa.Column("prompt_version", sa.String(length=40), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # --- market_segments ---------------------------------------------------
    op.create_table(
        "market_segments",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "market_map_id",
            sa.BigInteger(),
            sa.ForeignKey("talent_market_maps.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("segment_type", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(length=10), nullable=False, server_default="medium"),
        sa.Column(
            "coverage_status", sa.String(length=30), nullable=False, server_default="not_started"
        ),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "ai_suggested", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_market_segments_market_map_id", "market_segments", ["market_map_id"]
    )

    # --- target_companies --------------------------------------------------
    op.create_table(
        "target_companies",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "market_map_id",
            sa.BigInteger(),
            sa.ForeignKey("talent_market_maps.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "segment_id",
            sa.BigInteger(),
            sa.ForeignKey("market_segments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("industry", sa.String(length=120), nullable=True),
        sa.Column("priority", sa.String(length=10), nullable=False, server_default="medium"),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column(
            "coverage_status",
            sa.String(length=30),
            nullable=False,
            server_default="not_reviewed",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "ai_suggested", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_target_companies_market_map_id", "target_companies", ["market_map_id"]
    )

    # --- equivalent_roles --------------------------------------------------
    op.create_table(
        "equivalent_roles",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "market_map_id",
            sa.BigInteger(),
            sa.ForeignKey("talent_market_maps.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("seniority", sa.String(length=80), nullable=True),
        sa.Column("closeness", sa.String(length=10), nullable=False, server_default="medium"),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(length=10), nullable=False, server_default="medium"),
        sa.Column(
            "industries", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column(
            "ai_suggested", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_equivalent_roles_market_map_id", "equivalent_roles", ["market_map_id"]
    )

    # --- market_gaps -------------------------------------------------------
    op.create_table(
        "market_gaps",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "market_map_id",
            sa.BigInteger(),
            sa.ForeignKey("talent_market_maps.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("frequency", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_evaluated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("impact", sa.String(length=10), nullable=False, server_default="medium"),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_market_gaps_market_map_id", "market_gaps", ["market_map_id"])

    # --- recalibration_recommendations -------------------------------------
    op.create_table(
        "recalibration_recommendations",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "market_map_id",
            sa.BigInteger(),
            sa.ForeignKey("talent_market_maps.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("expected_impact", sa.Text(), nullable=True),
        sa.Column("confidence", sa.String(length=10), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(length=12), nullable=False, server_default="suggested"),
        sa.Column("generated_by", sa.String(length=20), nullable=False, server_default="rules"),
        sa.Column("acted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_recalibration_recommendations_market_map_id",
        "recalibration_recommendations",
        ["market_map_id"],
    )

    # --- market_map_candidate_overrides ------------------------------------
    op.create_table(
        "market_map_candidate_overrides",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "market_map_id",
            sa.BigInteger(),
            sa.ForeignKey("talent_market_maps.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "candidate_id",
            sa.Integer(),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "segment_id",
            sa.BigInteger(),
            sa.ForeignKey("market_segments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "target_company_id",
            sa.BigInteger(),
            sa.ForeignKey("target_companies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "equivalent_role_id",
            sa.BigInteger(),
            sa.ForeignKey("equivalent_roles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "market_map_id", "candidate_id", name="uq_mmco_map_candidate"
        ),
    )
    op.create_index(
        "ix_mmco_market_map_id",
        "market_map_candidate_overrides",
        ["market_map_id"],
    )
    op.create_index(
        "ix_mmco_candidate_id", "market_map_candidate_overrides", ["candidate_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_mmco_candidate_id", table_name="market_map_candidate_overrides")
    op.drop_index("ix_mmco_market_map_id", table_name="market_map_candidate_overrides")
    op.drop_table("market_map_candidate_overrides")

    op.drop_index(
        "ix_recalibration_recommendations_market_map_id",
        table_name="recalibration_recommendations",
    )
    op.drop_table("recalibration_recommendations")

    op.drop_index("ix_market_gaps_market_map_id", table_name="market_gaps")
    op.drop_table("market_gaps")

    op.drop_index("ix_equivalent_roles_market_map_id", table_name="equivalent_roles")
    op.drop_table("equivalent_roles")

    op.drop_index("ix_target_companies_market_map_id", table_name="target_companies")
    op.drop_table("target_companies")

    op.drop_index("ix_market_segments_market_map_id", table_name="market_segments")
    op.drop_table("market_segments")

    op.drop_table("talent_market_maps")
