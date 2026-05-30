from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


SegmentType = Literal["primary", "adjacent", "exploratory"]
PriorityLevel = Literal["high", "medium", "low"]
ClosenessLevel = Literal["high", "medium", "low"]
ImpactLevel = Literal["high", "medium", "low"]
ConfidenceLevel = Literal["high", "medium", "low"]
MapStatus = Literal["draft", "generated", "updated", "archived"]
MarketAssessment = Literal["broad", "moderate", "narrow", "very_narrow"]
SegmentCoverage = Literal[
    "not_started", "in_progress", "partially_covered", "covered", "discarded"
]
CompanyCoverage = Literal[
    "not_reviewed",
    "in_review",
    "partially_covered",
    "covered",
    "no_relevant_candidates",
    "discarded",
]
RecommendationStatus = Literal["suggested", "accepted", "rejected"]


# --- Sub-entidades: read -----------------------------------------------------


class MarketSegmentRead(BaseModel):
    id: int
    market_map_id: int
    name: str
    segment_type: SegmentType
    description: str | None
    priority: PriorityLevel
    coverage_status: SegmentCoverage
    rationale: str | None
    sort_order: int
    ai_suggested: bool
    created_at: datetime
    updated_at: datetime
    candidate_count: int = 0  # derivado

    model_config = {"from_attributes": True}


class TargetCompanyRead(BaseModel):
    id: int
    market_map_id: int
    segment_id: int | None
    name: str
    industry: str | None
    priority: PriorityLevel
    rationale: str | None
    coverage_status: CompanyCoverage
    notes: str | None
    ai_suggested: bool
    created_at: datetime
    updated_at: datetime
    candidates_identified: int = 0  # derivado
    candidates_evaluated: int = 0  # derivado
    high_fit_candidates: int = 0  # derivado

    model_config = {"from_attributes": True}


class EquivalentRoleRead(BaseModel):
    id: int
    market_map_id: int
    title: str
    seniority: str | None
    closeness: ClosenessLevel
    rationale: str | None
    priority: PriorityLevel
    industries: list[str] = Field(default_factory=list)
    ai_suggested: bool
    created_at: datetime
    updated_at: datetime
    candidate_count: int = 0  # derivado

    model_config = {"from_attributes": True}


class MarketGapRead(BaseModel):
    id: int
    market_map_id: int
    title: str
    frequency: int
    total_evaluated: int
    impact: ImpactLevel
    evidence: str | None
    recommendation: str | None
    detected_at: datetime

    model_config = {"from_attributes": True}


class RecalibrationRecommendationRead(BaseModel):
    id: int
    market_map_id: int
    title: str
    reason: str
    expected_impact: str | None
    confidence: ConfidenceLevel
    status: RecommendationStatus
    generated_by: Literal["rules", "ai"]
    acted_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Cobertura derivada ------------------------------------------------------


class CoverageStats(BaseModel):
    candidates_identified: int
    candidates_loaded: int
    candidates_evaluated: int
    high_fit: int
    medium_fit: int
    low_fit: int
    discarded: int
    shortlisted: int
    target_companies_total: int
    target_companies_reviewed: int
    target_companies_pending: int
    industries_covered: int
    coverage_pct: int  # 0..100


# --- Map read ---------------------------------------------------------------


class TalentMarketMapRead(BaseModel):
    id: int
    search_mandate_id: int
    position_spec_id: int | None
    status: MapStatus
    executive_summary: str | None
    executive_summary_for_client: str | None
    market_assessment: MarketAssessment | None
    generated_by_model: str | None
    prompt_version: str | None
    generated_at: datetime | None
    created_at: datetime
    updated_at: datetime
    segments: list[MarketSegmentRead] = Field(default_factory=list)
    companies: list[TargetCompanyRead] = Field(default_factory=list)
    equivalent_roles: list[EquivalentRoleRead] = Field(default_factory=list)
    gaps: list[MarketGapRead] = Field(default_factory=list)
    recommendations: list[RecalibrationRecommendationRead] = Field(default_factory=list)
    coverage: CoverageStats


# --- Payloads CRUD ---------------------------------------------------------


class MapUpdatePayload(BaseModel):
    executive_summary: str | None = None
    executive_summary_for_client: str | None = None
    market_assessment: MarketAssessment | None = None
    status: MapStatus | None = None


class SegmentCreatePayload(BaseModel):
    name: str = Field(..., max_length=200)
    segment_type: SegmentType
    description: str | None = None
    priority: PriorityLevel = "medium"
    coverage_status: SegmentCoverage = "not_started"
    rationale: str | None = None


class SegmentUpdatePayload(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    segment_type: SegmentType | None = None
    description: str | None = None
    priority: PriorityLevel | None = None
    coverage_status: SegmentCoverage | None = None
    rationale: str | None = None
    sort_order: int | None = None


class SegmentReorderPayload(BaseModel):
    ordered_ids: list[int] = Field(..., min_length=1)


class CompanyCreatePayload(BaseModel):
    name: str = Field(..., max_length=200)
    industry: str | None = Field(default=None, max_length=120)
    segment_id: int | None = None
    priority: PriorityLevel = "medium"
    rationale: str | None = None
    coverage_status: CompanyCoverage = "not_reviewed"
    notes: str | None = None


class CompanyUpdatePayload(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    industry: str | None = Field(default=None, max_length=120)
    segment_id: int | None = None
    priority: PriorityLevel | None = None
    rationale: str | None = None
    coverage_status: CompanyCoverage | None = None
    notes: str | None = None


class EquivalentRoleCreatePayload(BaseModel):
    title: str = Field(..., max_length=200)
    seniority: str | None = Field(default=None, max_length=80)
    closeness: ClosenessLevel = "medium"
    rationale: str | None = None
    priority: PriorityLevel = "medium"
    industries: list[str] = Field(default_factory=list)


class EquivalentRoleUpdatePayload(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    seniority: str | None = Field(default=None, max_length=80)
    closeness: ClosenessLevel | None = None
    rationale: str | None = None
    priority: PriorityLevel | None = None
    industries: list[str] | None = None


class MapCandidateRead(BaseModel):
    candidate_id: int
    full_name: str
    current_company: str | None
    current_position: str | None
    evaluation_score: int | None
    score_category: str | None
    auto_company_id: int | None
    segment_id: int | None
    target_company_id: int | None
    equivalent_role_id: int | None


class CandidateAssignPayload(BaseModel):
    segment_id: int | None = None
    target_company_id: int | None = None
    equivalent_role_id: int | None = None


class RecommendationDecisionPayload(BaseModel):
    status: Literal["accepted", "rejected"]


class GenerateMapPayload(BaseModel):
    """Opcionalmente pisar entidades AI suggeridas; default no pisa edits manuales."""

    overwrite_ai_suggested: bool = True
    overwrite_manual: bool = False
