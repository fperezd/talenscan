from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CandidateEvaluation(Base):
    __tablename__ = "candidate_evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False, index=True)
    position_spec_id: Mapped[int] = mapped_column(ForeignKey("position_specs.id"), nullable=False, index=True)
    total_score: Mapped[int] = mapped_column(nullable=False, default=0)
    score_category: Mapped[str] = mapped_column(String(80), nullable=False, default="Calce parcial")
    recommendation: Mapped[str] = mapped_column(String(180), nullable=False, default="Revisar brechas antes de avanzar")
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    dimension_scores: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False, default=list)
    critical_gaps: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False, default=list)
    strengths: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    weaknesses: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    risks: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    interview_questions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    supporting_evidence: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    final_verdict: Mapped[str] = mapped_column(String(120), nullable=False, default="Mantener en reserva")
    evaluation_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    model_version: Mapped[str] = mapped_column(String(80), nullable=False, default="talenscan-rules-v1")
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False, default="evaluation-v1")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
