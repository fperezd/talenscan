from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PositionSpec(Base):
    __tablename__ = "position_specs"

    id: Mapped[int] = mapped_column(primary_key=True)
    search_mandate_id: Mapped[int] = mapped_column(ForeignKey("search_mandates.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    role_mission: Mapped[str] = mapped_column(Text, nullable=False, default="")
    search_context: Mapped[str] = mapped_column(Text, nullable=False, default="")
    key_responsibilities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    expected_results: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    must_have_requirements: Mapped[list[dict[str, str | int | list[str]]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    nice_to_have_requirements: Mapped[list[dict[str, str | int | list[str]]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    technical_skills: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    functional_skills: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    leadership_skills: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    target_industries: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    target_company_types: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    equivalent_roles: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    market_mapping_hypothesis: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evaluation_criteria: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    interview_questions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    scoring_model: Mapped[list[dict[str, str | int]]] = mapped_column(JSON, nullable=False, default=list)
    red_flags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    validation_questions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    generated_by_model: Mapped[str] = mapped_column(String(120), nullable=False, default="talenscan-rules-v1")
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False, default="position-spec-v1")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
