from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False, index=True)
    candidate_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate_documents.id"), nullable=True, index=True
    )
    current_position: Mapped[str | None] = mapped_column(String(200), nullable=True)
    current_company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    total_years_experience: Mapped[int | None] = mapped_column(nullable=True)
    industries: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    roles: Mapped[list[dict[str, str | int | list[str]]]] = mapped_column(JSON, nullable=False, default=list)
    education: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    certifications: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    tools: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    languages: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    achievements: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    inferred_seniority: Mapped[str | None] = mapped_column(String(80), nullable=True)
    missing_information: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    evidence_snippets: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    parsed_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
