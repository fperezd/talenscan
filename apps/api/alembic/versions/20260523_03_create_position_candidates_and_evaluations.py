"""create position spec, candidates, documents, profiles and evaluations

Revision ID: 20260523_03
Revises: 20260523_02
Create Date: 2026-05-23
"""

from alembic import op
import sqlalchemy as sa


revision = "20260523_03"
down_revision = "20260523_02"
branch_labels = None
depends_on = None


json_empty_list = sa.text("'[]'::json")
json_empty_object = sa.text("'{}'::json")


def upgrade() -> None:
    op.create_table(
        "position_specs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("search_mandate_id", sa.Integer(), sa.ForeignKey("search_mandates.id"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("executive_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("role_mission", sa.Text(), nullable=False, server_default=""),
        sa.Column("search_context", sa.Text(), nullable=False, server_default=""),
        sa.Column("key_responsibilities", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("expected_results", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("must_have_requirements", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("nice_to_have_requirements", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("technical_skills", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("functional_skills", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("leadership_skills", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("target_industries", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("target_company_types", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("equivalent_roles", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("market_mapping_hypothesis", sa.Text(), nullable=False, server_default=""),
        sa.Column("evaluation_criteria", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("interview_questions", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("scoring_model", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("red_flags", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("validation_questions", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("generated_by_model", sa.String(length=120), nullable=False, server_default="talenscan-rules-v1"),
        sa.Column("prompt_version", sa.String(length=50), nullable=False, server_default="position-spec-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_position_specs_search_mandate_id", "position_specs", ["search_mandate_id"])

    op.create_table(
        "candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=200), nullable=True),
        sa.Column("phone", sa.String(length=80), nullable=True),
        sa.Column("linkedin_url", sa.String(length=400), nullable=True),
        sa.Column("current_position", sa.String(length=200), nullable=True),
        sa.Column("current_company", sa.String(length=200), nullable=True),
        sa.Column("country", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "candidate_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=40), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("file_url", sa.String(length=500), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("text_extraction_status", sa.String(length=80), nullable=False, server_default="Recibido"),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_candidate_documents_candidate_id", "candidate_documents", ["candidate_id"])

    op.create_table(
        "candidate_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("candidate_document_id", sa.Integer(), sa.ForeignKey("candidate_documents.id"), nullable=False),
        sa.Column("current_position", sa.String(length=200), nullable=True),
        sa.Column("current_company", sa.String(length=200), nullable=True),
        sa.Column("total_years_experience", sa.Integer(), nullable=True),
        sa.Column("industries", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("roles", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("education", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("certifications", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("tools", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("languages", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("achievements", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("inferred_seniority", sa.String(length=80), nullable=True),
        sa.Column("missing_information", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("evidence_snippets", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("parsed_json", sa.JSON(), nullable=False, server_default=json_empty_object),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_candidate_profiles_candidate_id", "candidate_profiles", ["candidate_id"])
    op.create_index("ix_candidate_profiles_candidate_document_id", "candidate_profiles", ["candidate_document_id"])

    op.create_table(
        "candidate_evaluations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("position_spec_id", sa.Integer(), sa.ForeignKey("position_specs.id"), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score_category", sa.String(length=80), nullable=False, server_default="Calce parcial"),
        sa.Column(
            "recommendation",
            sa.String(length=180),
            nullable=False,
            server_default="Revisar brechas antes de avanzar",
        ),
        sa.Column("executive_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("dimension_scores", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("critical_gaps", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("strengths", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("weaknesses", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("risks", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("interview_questions", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("supporting_evidence", sa.JSON(), nullable=False, server_default=json_empty_list),
        sa.Column("final_verdict", sa.String(length=120), nullable=False, server_default="Mantener en reserva"),
        sa.Column("evaluation_json", sa.JSON(), nullable=False, server_default=json_empty_object),
        sa.Column("model_version", sa.String(length=80), nullable=False, server_default="talenscan-rules-v1"),
        sa.Column("prompt_version", sa.String(length=80), nullable=False, server_default="evaluation-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_candidate_evaluations_candidate_id", "candidate_evaluations", ["candidate_id"])
    op.create_index("ix_candidate_evaluations_position_spec_id", "candidate_evaluations", ["position_spec_id"])


def downgrade() -> None:
    op.drop_index("ix_candidate_evaluations_position_spec_id", table_name="candidate_evaluations")
    op.drop_index("ix_candidate_evaluations_candidate_id", table_name="candidate_evaluations")
    op.drop_table("candidate_evaluations")

    op.drop_index("ix_candidate_profiles_candidate_document_id", table_name="candidate_profiles")
    op.drop_index("ix_candidate_profiles_candidate_id", table_name="candidate_profiles")
    op.drop_table("candidate_profiles")

    op.drop_index("ix_candidate_documents_candidate_id", table_name="candidate_documents")
    op.drop_table("candidate_documents")

    op.drop_table("candidates")

    op.drop_index("ix_position_specs_search_mandate_id", table_name="position_specs")
    op.drop_table("position_specs")
