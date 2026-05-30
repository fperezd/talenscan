"""Schemas de la Bóveda de Talento."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


TalentStatus = Literal["active", "passive", "placed", "archived"]
AvailabilityStatus = Literal[
    "unknown", "available", "open_to_offers", "not_available", "placed"
]
NoteType = Literal["general", "call", "meeting", "client_feedback", "interview", "alert"]
DocumentType = Literal["cv", "report", "portfolio", "certificate", "other"]


# --- Sub-entidades read -----------------------------------------------------


class TalentTagRead(BaseModel):
    id: int
    name: str
    category: str | None = None

    model_config = {"from_attributes": True}


class TalentNoteRead(BaseModel):
    id: int
    talent_profile_id: int
    search_mandate_id: int | None
    note_type: NoteType
    note_text: str
    created_by: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TalentDocumentRead(BaseModel):
    id: int
    talent_profile_id: int
    candidate_document_id: int | None
    document_type: str
    file_name: str | None
    file_url: str | None
    source: str | None
    uploaded_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TalentEvaluationRead(BaseModel):
    id: int
    talent_profile_id: int
    candidate_evaluation_id: int | None
    search_mandate_id: int | None
    position_spec_id: int | None
    client_name: str | None
    target_role: str | None
    total_score: int | None
    score_category: str | None
    recommendation: str | None
    critical_gaps: list[Any] = Field(default_factory=list)
    strengths: list[Any] = Field(default_factory=list)
    weaknesses: list[Any] = Field(default_factory=list)
    risks: list[Any] = Field(default_factory=list)
    result_stage: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TalentProcessHistoryRead(BaseModel):
    id: int
    talent_profile_id: int
    search_mandate_id: int | None
    client_name: str | None
    target_role: str | None
    pipeline_stage: str | None
    final_result: str | None
    discard_reason: str | None
    client_feedback: str | None
    consultant_notes: str | None
    started_at: datetime | None
    ended_at: datetime | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class TalentProfileVersionRead(BaseModel):
    id: int
    talent_profile_id: int
    version_number: int
    change_reason: str | None
    source: str | None
    created_by: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Talent profile read ----------------------------------------------------


class TalentProfileSummary(BaseModel):
    """Fila de la lista /talentos."""

    id: int
    full_name: str
    current_position: str | None
    current_company: str | None
    inferred_seniority: str | None
    country: str | None
    city: str | None
    industries: list[Any] = Field(default_factory=list)
    skills: list[Any] = Field(default_factory=list)
    status: TalentStatus
    availability_status: AvailabilityStatus
    do_not_contact: bool
    last_score: int | None = None
    last_evaluated_at: datetime | None = None
    tags: list[TalentTagRead] = Field(default_factory=list)
    evaluations_count: int = 0
    updated_at: datetime

    model_config = {"from_attributes": True}


class TalentProfileRead(BaseModel):
    id: int
    origin_candidate_id: int | None
    full_name: str
    primary_email: str | None
    primary_phone: str | None
    linkedin_url: str | None
    current_position: str | None
    current_company: str | None
    country: str | None
    city: str | None
    general_location: str | None
    inferred_seniority: str | None
    summary: str | None
    industries: list[Any] = Field(default_factory=list)
    skills: list[Any] = Field(default_factory=list)
    tools: list[Any] = Field(default_factory=list)
    languages: list[Any] = Field(default_factory=list)
    certifications: list[Any] = Field(default_factory=list)
    education: list[Any] = Field(default_factory=list)
    career_history: list[Any] = Field(default_factory=list)
    achievements: list[Any] = Field(default_factory=list)
    status: TalentStatus
    availability_status: AvailabilityStatus
    expected_compensation: dict[str, Any] | None
    do_not_contact: bool
    last_contacted_at: datetime | None
    last_evaluated_at: datetime | None
    created_at: datetime
    updated_at: datetime
    # Relaciones consolidadas
    tags: list[TalentTagRead] = Field(default_factory=list)
    documents: list[TalentDocumentRead] = Field(default_factory=list)
    evaluations: list[TalentEvaluationRead] = Field(default_factory=list)
    process_history: list[TalentProcessHistoryRead] = Field(default_factory=list)
    notes: list[TalentNoteRead] = Field(default_factory=list)
    versions: list[TalentProfileVersionRead] = Field(default_factory=list)


class TalentVaultMetrics(BaseModel):
    total: int
    evaluated: int
    in_reserve: int
    available: int
    average_score: int | None
    updated_last_30_days: int


class TalentProfileListResponse(BaseModel):
    items: list[TalentProfileSummary]
    total: int
    page: int
    page_size: int
    metrics: TalentVaultMetrics


# --- Payloads ---------------------------------------------------------------


class TalentProfileCreate(BaseModel):
    full_name: str = Field(..., max_length=200)
    primary_email: str | None = Field(default=None, max_length=200)
    primary_phone: str | None = Field(default=None, max_length=60)
    linkedin_url: str | None = Field(default=None, max_length=400)
    current_position: str | None = Field(default=None, max_length=200)
    current_company: str | None = Field(default=None, max_length=200)
    country: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    inferred_seniority: str | None = Field(default=None, max_length=80)
    summary: str | None = None
    industries: list[Any] = Field(default_factory=list)
    skills: list[Any] = Field(default_factory=list)
    tools: list[Any] = Field(default_factory=list)
    languages: list[Any] = Field(default_factory=list)
    status: TalentStatus = "active"
    availability_status: AvailabilityStatus = "unknown"
    do_not_contact: bool = False
    origin_candidate_id: int | None = None


class TalentProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=200)
    primary_email: str | None = Field(default=None, max_length=200)
    primary_phone: str | None = Field(default=None, max_length=60)
    linkedin_url: str | None = Field(default=None, max_length=400)
    current_position: str | None = Field(default=None, max_length=200)
    current_company: str | None = Field(default=None, max_length=200)
    country: str | None = None
    city: str | None = None
    general_location: str | None = None
    inferred_seniority: str | None = None
    summary: str | None = None
    industries: list[Any] | None = None
    skills: list[Any] | None = None
    tools: list[Any] | None = None
    languages: list[Any] | None = None
    certifications: list[Any] | None = None
    education: list[Any] | None = None
    career_history: list[Any] | None = None
    achievements: list[Any] | None = None
    status: TalentStatus | None = None
    availability_status: AvailabilityStatus | None = None
    expected_compensation: dict[str, Any] | None = None
    do_not_contact: bool | None = None
    change_reason: str | None = None  # para versionamiento


class NoteCreatePayload(BaseModel):
    note_type: NoteType = "general"
    note_text: str = Field(..., min_length=1)
    search_mandate_id: int | None = None
    created_by: str | None = None


class NoteUpdatePayload(BaseModel):
    note_type: NoteType | None = None
    note_text: str | None = None


class TagAssignPayload(BaseModel):
    name: str = Field(..., max_length=80)
    category: str | None = Field(default=None, max_length=60)


class DuplicateDetectPayload(BaseModel):
    full_name: str | None = None
    primary_email: str | None = None
    primary_phone: str | None = None
    linkedin_url: str | None = None
    current_company: str | None = None


class DuplicateMatch(BaseModel):
    talent_profile_id: int
    match_score: float
    match_reasons: list[str]
    full_name: str
    current_company: str | None
    current_position: str | None


class DuplicateDetectResponse(BaseModel):
    has_potential_duplicates: bool
    matches: list[DuplicateMatch]


class EvaluateAgainstMandatePayload(BaseModel):
    search_mandate_id: int
    position_spec_id: int | None = None
    use_latest_candidate_profile: bool = True
    add_to_pipeline: bool = True
    initial_pipeline_stage: str = "evaluated"
