from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


PIPELINE_STAGES = (
    "received",
    "analyzing",
    "evaluated",
    "preselected",
    "interview",
    "reserve",
    "discarded",
    "present_to_client",
)


class CandidatePipelineItem(Base):
    __tablename__ = "candidate_pipeline_items"
    __table_args__ = (
        UniqueConstraint("mandate_id", "candidate_id", name="uq_pipeline_mandate_candidate"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    mandate_id: Mapped[int] = mapped_column(ForeignKey("search_mandates.id"), nullable=False, index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False, index=True)
    evaluation_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate_evaluations.id"), nullable=True, index=True
    )
    stage: Mapped[str] = mapped_column(String(40), nullable=False, default="received", index=True)
    stage_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_priority: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_shortlisted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consultant_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    discard_reason: Mapped[str] = mapped_column(String(240), nullable=False, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    last_moved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
