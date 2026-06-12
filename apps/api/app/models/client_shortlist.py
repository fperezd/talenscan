from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# Estados aceptados para el feedback del cliente.
# Mantenemos los 3 históricos para retrocompat y añadimos los 5 de Decision Room.
CLIENT_FEEDBACK_STATUSES = (
    # Históricos (v1 de shortlist)
    "interested",
    "not_interested",
    "want_interview",
    # Decision Room
    "favorite",
    "interview_requested",
    "more_info_requested",
    "keep_in_review",
    "rejected",
)

DECISION_ROOM_STATUSES = (
    "draft",
    "ready_to_share",
    "invitation_sent",
    "viewed",
    "in_review",
    "feedback_received",
    "closed",
    "expired",
)

DECISION_ROOM_RECOMMENDATIONS = (
    "highly_recommended",
    "recommended",
    "recommended_with_validations",
    "reserve",
    "not_recommended",
)

DECISION_ROOM_EVIDENCE_LEVELS = ("high", "medium", "low")


class ClientShortlist(Base):
    """Decision Room — sala privada de decisión compartida con el cliente.

    Mantiene el nombre `ClientShortlist` por compatibilidad con datos y
    endpoints previos; en UI y conceptualmente es un Decision Room.
    """

    __tablename__ = "client_shortlists"

    id: Mapped[int] = mapped_column(primary_key=True)
    mandate_id: Mapped[int] = mapped_column(
        ForeignKey("search_mandates.id"), nullable=False, index=True
    )
    public_token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="Shortlist TalentScan")
    message_to_client: Mapped[str] = mapped_column(Text, nullable=False, default="")
    show_scores: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    viewed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- Decision Room enrichment ------------------------------------------
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft")
    client_contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    client_contact_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    client_contact_company: Mapped[str | None] = mapped_column(String(200), nullable=True)

    access_code_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    access_code_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Falso por default → los shortlists pre-existentes no exigen código.
    # El consultor activa el gate al configurar el room.
    access_code_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_invitation_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    intro_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    show_availability: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    show_salary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    show_risks: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    show_comparison: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allow_comments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allow_rating: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allow_report_download: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ClientShortlistItem(Base):
    __tablename__ = "client_shortlist_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    shortlist_id: Mapped[int] = mapped_column(
        ForeignKey("client_shortlists.id"), nullable=False, index=True
    )
    evaluation_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate_evaluations.id"), nullable=True, index=True
    )
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id"), nullable=False, index=True
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    client_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    client_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # --- Decision Room: overrides editables por el consultor ---------------
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recommendation: Mapped[str | None] = mapped_column(String(40), nullable=True)
    consultant_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_fits: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    risks_or_validations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    evidence_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    availability: Mapped[str | None] = mapped_column(String(200), nullable=True)
    salary_expectation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    salary_share_authorized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


DECISION_ROOM_EVENT_TYPES = (
    "room_created",
    "candidate_added",
    "candidate_removed",
    "candidate_reordered",
    "candidate_pinned",
    "candidate_unpinned",
    "link_generated",
    "code_generated",
    "invitation_sent",
    "invitation_copied",
    "link_opened",
    "code_validated",
    "code_rejected",
    "client_entered",
    "client_viewed_candidate",
    "client_favorited",
    "client_requested_interview",
    "client_requested_more_info",
    "client_kept_in_review",
    "client_rejected_candidate",
    "client_commented",
    "client_rated",
    "access_expired",
    "link_regenerated",
    "room_closed",
    "room_config_updated",
    "item_overrides_updated",
)


class DecisionRoomEvent(Base):
    """Timeline interno del Decision Room. No visible para el cliente."""

    __tablename__ = "decision_room_events"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    shortlist_id: Mapped[int] = mapped_column(
        ForeignKey("client_shortlists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id: Mapped[int | None] = mapped_column(
        ForeignKey("client_shortlist_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    event_label: Mapped[str] = mapped_column(String(200), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    actor_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    event_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
