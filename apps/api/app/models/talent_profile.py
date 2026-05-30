"""Bóveda de Talento — Perfil Maestro de Talento y entidades asociadas.

Base inteligente, trazable y reutilizable de perfiles evaluados históricamente.

Entidades:
- TalentProfile: ficha única y viva de una persona (entidad principal).
- TalentDocument: documentos (CVs, etc.) asociados al perfil maestro.
- TalentEvaluation: referencias a Evaluaciones 360 históricas del talento.
- TalentProcessHistory: mandatos/procesos en que participó.
- TalentNote: notas internas del consultor.
- TalentTag + TalentProfileTag: catálogo de tags y relación N:N.
- TalentProfileVersion: snapshots/versionamiento del perfil.

Nota de adaptación: la spec sugiere PK UUID, pero todo el codebase usa PKs
enteros (con FKs int a candidates/search_mandates/etc.). Para consistencia y
para no romper relaciones existentes, se usan PKs enteros (patrón _BigPk, igual
que talent_market_map). Las referencias a entidades existentes son FK nullable
con ON DELETE SET NULL: la Bóveda preserva su historia aunque se borre el
registro origen.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# --- Vocabularios -----------------------------------------------------------

TALENT_STATUSES = ("active", "passive", "placed", "archived")
AVAILABILITY_STATUSES = (
    "unknown",
    "available",
    "open_to_offers",
    "not_available",
    "placed",
)
NOTE_TYPES = ("general", "call", "meeting", "client_feedback", "interview", "alert")
DOCUMENT_TYPES = ("cv", "report", "portfolio", "certificate", "other")

# Helper para mantener compatibilidad SQLite (tests) + Postgres (prod).
_BigPk = lambda: BigInteger().with_variant(Integer, "sqlite")  # noqa: E731


class TalentProfile(Base):
    """Perfil Maestro de Talento. Ficha única y viva de una persona."""

    __tablename__ = "talent_profiles"

    id: Mapped[int] = mapped_column(_BigPk(), primary_key=True, autoincrement=True)
    # Candidato origen (no rompe nada; ayuda a dedup y reutilización).
    origin_candidate_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True, index=True
    )

    full_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    primary_email: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    primary_phone: Mapped[str | None] = mapped_column(String(60), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(400), nullable=True, index=True)
    current_position: Mapped[str | None] = mapped_column(String(200), nullable=True)
    current_company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    general_location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    inferred_seniority: Mapped[str | None] = mapped_column(String(80), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    industries: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    skills: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    tools: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    languages: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    certifications: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    education: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    career_history: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    achievements: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    availability_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unknown"
    )
    expected_compensation: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    tags_snapshot: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    do_not_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    last_contacted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_evaluated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class TalentDocument(Base):
    __tablename__ = "talent_documents"

    id: Mapped[int] = mapped_column(_BigPk(), primary_key=True, autoincrement=True)
    talent_profile_id: Mapped[int] = mapped_column(
        ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate_documents.id", ondelete="SET NULL"), nullable=True
    )
    document_type: Mapped[str] = mapped_column(String(30), nullable=False, default="cv")
    file_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    file_url: Mapped[str | None] = mapped_column(String(600), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TalentEvaluation(Base):
    """Referencia a una Evaluación 360 histórica asociada al talento."""

    __tablename__ = "talent_evaluations"

    id: Mapped[int] = mapped_column(_BigPk(), primary_key=True, autoincrement=True)
    talent_profile_id: Mapped[int] = mapped_column(
        ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_evaluation_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate_evaluations.id", ondelete="SET NULL"), nullable=True
    )
    search_mandate_id: Mapped[int | None] = mapped_column(
        ForeignKey("search_mandates.id", ondelete="SET NULL"), nullable=True
    )
    position_spec_id: Mapped[int | None] = mapped_column(
        ForeignKey("position_specs.id", ondelete="SET NULL"), nullable=True
    )
    client_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    target_role: Mapped[str | None] = mapped_column(String(200), nullable=True)
    total_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    recommendation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    critical_gaps: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    strengths: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    weaknesses: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    risks: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    result_stage: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TalentProcessHistory(Base):
    __tablename__ = "talent_process_history"

    id: Mapped[int] = mapped_column(_BigPk(), primary_key=True, autoincrement=True)
    talent_profile_id: Mapped[int] = mapped_column(
        ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    search_mandate_id: Mapped[int | None] = mapped_column(
        ForeignKey("search_mandates.id", ondelete="SET NULL"), nullable=True
    )
    client_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    target_role: Mapped[str | None] = mapped_column(String(200), nullable=True)
    pipeline_stage: Mapped[str | None] = mapped_column(String(60), nullable=True)
    final_result: Mapped[str | None] = mapped_column(String(120), nullable=True)
    discard_reason: Mapped[str | None] = mapped_column(String(240), nullable=True)
    client_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    consultant_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class TalentNote(Base):
    __tablename__ = "talent_notes"

    id: Mapped[int] = mapped_column(_BigPk(), primary_key=True, autoincrement=True)
    talent_profile_id: Mapped[int] = mapped_column(
        ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    search_mandate_id: Mapped[int | None] = mapped_column(
        ForeignKey("search_mandates.id", ondelete="SET NULL"), nullable=True
    )
    note_type: Mapped[str] = mapped_column(String(30), nullable=False, default="general")
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class TalentTag(Base):
    __tablename__ = "talent_tags"
    __table_args__ = (UniqueConstraint("name", name="uq_talent_tag_name"),)

    id: Mapped[int] = mapped_column(_BigPk(), primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TalentProfileTag(Base):
    """Relación N:N entre talentos y tags."""

    __tablename__ = "talent_profile_tags"
    __table_args__ = (
        UniqueConstraint("talent_profile_id", "tag_id", name="uq_talent_profile_tag"),
    )

    id: Mapped[int] = mapped_column(_BigPk(), primary_key=True, autoincrement=True)
    talent_profile_id: Mapped[int] = mapped_column(
        ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("talent_tags.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TalentProfileVersion(Base):
    """Snapshot/versionamiento del perfil ante cambios críticos."""

    __tablename__ = "talent_profile_versions"

    id: Mapped[int] = mapped_column(_BigPk(), primary_key=True, autoincrement=True)
    talent_profile_id: Mapped[int] = mapped_column(
        ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    change_reason: Mapped[str | None] = mapped_column(String(240), nullable=True)
    source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
