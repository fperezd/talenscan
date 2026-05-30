"""create talent vault (bóveda de talento) tables

Revision ID: 20260530_10
Revises: 20260529_09
Create Date: 2026-05-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "20260530_10"
down_revision = "20260529_09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- talent_profiles ---------------------------------------------------
    op.create_table(
        "talent_profiles",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "origin_candidate_id",
            sa.Integer(),
            sa.ForeignKey("candidates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("primary_email", sa.String(length=200), nullable=True),
        sa.Column("primary_phone", sa.String(length=60), nullable=True),
        sa.Column("linkedin_url", sa.String(length=400), nullable=True),
        sa.Column("current_position", sa.String(length=200), nullable=True),
        sa.Column("current_company", sa.String(length=200), nullable=True),
        sa.Column("country", sa.String(length=120), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("general_location", sa.String(length=200), nullable=True),
        sa.Column("inferred_seniority", sa.String(length=80), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("industries", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("skills", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("tools", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("languages", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("certifications", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("education", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("career_history", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("achievements", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column(
            "availability_status", sa.String(length=20), nullable=False, server_default="unknown"
        ),
        sa.Column("expected_compensation", JSONB(), nullable=True),
        sa.Column("tags_snapshot", JSONB(), nullable=True),
        sa.Column("do_not_contact", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_contacted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_talent_profiles_full_name", "talent_profiles", ["full_name"])
    op.create_index("ix_talent_profiles_primary_email", "talent_profiles", ["primary_email"])
    op.create_index("ix_talent_profiles_linkedin_url", "talent_profiles", ["linkedin_url"])
    op.create_index("ix_talent_profiles_origin_candidate_id", "talent_profiles", ["origin_candidate_id"])

    # --- talent_documents --------------------------------------------------
    op.create_table(
        "talent_documents",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "talent_profile_id",
            sa.BigInteger(),
            sa.ForeignKey("talent_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "candidate_document_id",
            sa.Integer(),
            sa.ForeignKey("candidate_documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("document_type", sa.String(length=30), nullable=False, server_default="cv"),
        sa.Column("file_name", sa.String(length=300), nullable=True),
        sa.Column("file_url", sa.String(length=600), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("parsed_json", JSONB(), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_talent_documents_talent_profile_id", "talent_documents", ["talent_profile_id"])

    # --- talent_evaluations ------------------------------------------------
    op.create_table(
        "talent_evaluations",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "talent_profile_id",
            sa.BigInteger(),
            sa.ForeignKey("talent_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "candidate_evaluation_id",
            sa.Integer(),
            sa.ForeignKey("candidate_evaluations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "search_mandate_id",
            sa.Integer(),
            sa.ForeignKey("search_mandates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "position_spec_id",
            sa.Integer(),
            sa.ForeignKey("position_specs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("client_name", sa.String(length=200), nullable=True),
        sa.Column("target_role", sa.String(length=200), nullable=True),
        sa.Column("total_score", sa.Integer(), nullable=True),
        sa.Column("score_category", sa.String(length=80), nullable=True),
        sa.Column("recommendation", sa.String(length=200), nullable=True),
        sa.Column("critical_gaps", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("strengths", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("weaknesses", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("risks", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("result_stage", sa.String(length=60), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_talent_evaluations_talent_profile_id", "talent_evaluations", ["talent_profile_id"])

    # --- talent_process_history --------------------------------------------
    op.create_table(
        "talent_process_history",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "talent_profile_id",
            sa.BigInteger(),
            sa.ForeignKey("talent_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "search_mandate_id",
            sa.Integer(),
            sa.ForeignKey("search_mandates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("client_name", sa.String(length=200), nullable=True),
        sa.Column("target_role", sa.String(length=200), nullable=True),
        sa.Column("pipeline_stage", sa.String(length=60), nullable=True),
        sa.Column("final_result", sa.String(length=120), nullable=True),
        sa.Column("discard_reason", sa.String(length=240), nullable=True),
        sa.Column("client_feedback", sa.Text(), nullable=True),
        sa.Column("consultant_notes", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_talent_process_history_talent_profile_id", "talent_process_history", ["talent_profile_id"]
    )

    # --- talent_notes ------------------------------------------------------
    op.create_table(
        "talent_notes",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "talent_profile_id",
            sa.BigInteger(),
            sa.ForeignKey("talent_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "search_mandate_id",
            sa.Integer(),
            sa.ForeignKey("search_mandates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("note_type", sa.String(length=30), nullable=False, server_default="general"),
        sa.Column("note_text", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_talent_notes_talent_profile_id", "talent_notes", ["talent_profile_id"])

    # --- talent_tags + talent_profile_tags ---------------------------------
    op.create_table(
        "talent_tags",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("category", sa.String(length=60), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_talent_tag_name"),
    )

    op.create_table(
        "talent_profile_tags",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "talent_profile_id",
            sa.BigInteger(),
            sa.ForeignKey("talent_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tag_id",
            sa.BigInteger(),
            sa.ForeignKey("talent_tags.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("talent_profile_id", "tag_id", name="uq_talent_profile_tag"),
    )
    op.create_index("ix_talent_profile_tags_talent_profile_id", "talent_profile_tags", ["talent_profile_id"])
    op.create_index("ix_talent_profile_tags_tag_id", "talent_profile_tags", ["tag_id"])

    # --- talent_profile_versions -------------------------------------------
    op.create_table(
        "talent_profile_versions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "talent_profile_id",
            sa.BigInteger(),
            sa.ForeignKey("talent_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("snapshot_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("change_reason", sa.String(length=240), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=True),
        sa.Column("created_by", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_talent_profile_versions_talent_profile_id", "talent_profile_versions", ["talent_profile_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_talent_profile_versions_talent_profile_id", table_name="talent_profile_versions")
    op.drop_table("talent_profile_versions")
    op.drop_index("ix_talent_profile_tags_tag_id", table_name="talent_profile_tags")
    op.drop_index("ix_talent_profile_tags_talent_profile_id", table_name="talent_profile_tags")
    op.drop_table("talent_profile_tags")
    op.drop_table("talent_tags")
    op.drop_index("ix_talent_notes_talent_profile_id", table_name="talent_notes")
    op.drop_table("talent_notes")
    op.drop_index("ix_talent_process_history_talent_profile_id", table_name="talent_process_history")
    op.drop_table("talent_process_history")
    op.drop_index("ix_talent_evaluations_talent_profile_id", table_name="talent_evaluations")
    op.drop_table("talent_evaluations")
    op.drop_index("ix_talent_documents_talent_profile_id", table_name="talent_documents")
    op.drop_table("talent_documents")
    op.drop_index("ix_talent_profiles_origin_candidate_id", table_name="talent_profiles")
    op.drop_index("ix_talent_profiles_linkedin_url", table_name="talent_profiles")
    op.drop_index("ix_talent_profiles_primary_email", table_name="talent_profiles")
    op.drop_index("ix_talent_profiles_full_name", table_name="talent_profiles")
    op.drop_table("talent_profiles")
