"""Talent Market Map — mapa estratégico del mercado de talento por mandato.

Estructura:
- TalentMarketMap (1:1 con SearchMandate)
- MarketSegment (primary / adjacent / exploratory)
- TargetCompany (asociada a segmento opcionalmente)
- EquivalentRole
- MarketGap (calculadas determinísticamente desde CandidateEvaluation.critical_gaps)
- RecalibrationRecommendation (motor de reglas + IA opcional)
- MarketMapCandidateOverride (pivote para asignaciones manuales del consultor)
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


SEGMENT_TYPES = ("primary", "adjacent", "exploratory")
PRIORITY_LEVELS = ("high", "medium", "low")
CLOSENESS_LEVELS = ("high", "medium", "low")
IMPACT_LEVELS = ("high", "medium", "low")
CONFIDENCE_LEVELS = ("high", "medium", "low")

MAP_STATUSES = ("draft", "generated", "updated", "archived")
MARKET_ASSESSMENTS = ("broad", "moderate", "narrow", "very_narrow")
SEGMENT_COVERAGE_STATUSES = (
    "not_started",
    "in_progress",
    "partially_covered",
    "covered",
    "discarded",
)
COMPANY_COVERAGE_STATUSES = (
    "not_reviewed",
    "in_review",
    "partially_covered",
    "covered",
    "no_relevant_candidates",
    "discarded",
)
RECOMMENDATION_STATUSES = ("suggested", "accepted", "rejected")
RECOMMENDATION_GENERATORS = ("rules", "ai")


# Helper para mantener compatibilidad SQLite (tests) + Postgres (prod).
_BigPk = lambda: BigInteger().with_variant(Integer, "sqlite")  # noqa: E731


class TalentMarketMap(Base):
    __tablename__ = "talent_market_maps"

    id: Mapped[int] = mapped_column(_BigPk(), primary_key=True, autoincrement=True)
    search_mandate_id: Mapped[int] = mapped_column(
        ForeignKey("search_mandates.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    position_spec_id: Mapped[int | None] = mapped_column(
        ForeignKey("position_specs.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    executive_summary_for_client: Mapped[str | None] = mapped_column(Text, nullable=True)
    market_assessment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    generated_by_model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class MarketSegment(Base):
    __tablename__ = "market_segments"

    id: Mapped[int] = mapped_column(_BigPk(), primary_key=True, autoincrement=True)
    market_map_id: Mapped[int] = mapped_column(
        ForeignKey("talent_market_maps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    segment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    coverage_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="not_started"
    )
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_suggested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TargetCompany(Base):
    __tablename__ = "target_companies"

    id: Mapped[int] = mapped_column(_BigPk(), primary_key=True, autoincrement=True)
    market_map_id: Mapped[int] = mapped_column(
        ForeignKey("talent_market_maps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_id: Mapped[int | None] = mapped_column(
        ForeignKey("market_segments.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    coverage_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="not_reviewed"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_suggested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class EquivalentRole(Base):
    __tablename__ = "equivalent_roles"

    id: Mapped[int] = mapped_column(_BigPk(), primary_key=True, autoincrement=True)
    market_map_id: Mapped[int] = mapped_column(
        ForeignKey("talent_market_maps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    seniority: Mapped[str | None] = mapped_column(String(80), nullable=True)
    closeness: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    industries: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    ai_suggested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class MarketGap(Base):
    """Brecha detectada determinísticamente desde CandidateEvaluation.critical_gaps.

    No tiene updated_at: la tabla se reescribe entera cada vez que se recalcula.
    """

    __tablename__ = "market_gaps"

    id: Mapped[int] = mapped_column(_BigPk(), primary_key=True, autoincrement=True)
    market_map_id: Mapped[int] = mapped_column(
        ForeignKey("talent_market_maps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    frequency: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_evaluated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    impact: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RecalibrationRecommendation(Base):
    __tablename__ = "recalibration_recommendations"

    id: Mapped[int] = mapped_column(_BigPk(), primary_key=True, autoincrement=True)
    market_map_id: Mapped[int] = mapped_column(
        ForeignKey("talent_market_maps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    expected_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="suggested")
    generated_by: Mapped[str] = mapped_column(String(20), nullable=False, default="rules")
    acted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MarketMapCandidateOverride(Base):
    """Pivote para asociaciones explícitas candidato ↔ segmento/empresa/rol.

    Las asociaciones automáticas (por matching de candidate.current_company con
    target_companies.name) se calculan en tiempo real en build_view.
    """

    __tablename__ = "market_map_candidate_overrides"
    __table_args__ = (
        UniqueConstraint("market_map_id", "candidate_id", name="uq_mmco_map_candidate"),
    )

    id: Mapped[int] = mapped_column(_BigPk(), primary_key=True, autoincrement=True)
    market_map_id: Mapped[int] = mapped_column(
        ForeignKey("talent_market_maps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_id: Mapped[int | None] = mapped_column(
        ForeignKey("market_segments.id", ondelete="SET NULL"), nullable=True
    )
    target_company_id: Mapped[int | None] = mapped_column(
        ForeignKey("target_companies.id", ondelete="SET NULL"), nullable=True
    )
    equivalent_role_id: Mapped[int | None] = mapped_column(
        ForeignKey("equivalent_roles.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
