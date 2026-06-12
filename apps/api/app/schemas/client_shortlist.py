from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


# --- Admin payloads ---------------------------------------------------------


class ClientShortlistCreate(BaseModel):
    title: str = Field(default="Shortlist TalentScan", max_length=200)
    message_to_client: str = ""
    intro_message: str | None = None
    show_scores: bool = False
    show_availability: bool = False
    show_salary: bool = False
    show_risks: bool = False
    show_comparison: bool = True
    allow_comments: bool = True
    allow_rating: bool = False
    allow_report_download: bool = False
    access_code_required: bool = False
    evaluation_ids: list[int] = Field(..., min_length=1, max_length=10)
    expires_at: datetime | None = None
    client_contact_name: str | None = Field(default=None, max_length=200)
    client_contact_email: str | None = Field(default=None, max_length=200)
    client_contact_company: str | None = Field(default=None, max_length=200)


class ClientShortlistConfigUpdate(BaseModel):
    """PATCH parcial — el consultor edita configuración del room."""

    title: str | None = Field(default=None, max_length=200)
    message_to_client: str | None = None
    intro_message: str | None = None
    show_scores: bool | None = None
    show_availability: bool | None = None
    show_salary: bool | None = None
    show_risks: bool | None = None
    show_comparison: bool | None = None
    allow_comments: bool | None = None
    allow_rating: bool | None = None
    allow_report_download: bool | None = None
    access_code_required: bool | None = None
    expires_at: datetime | None = None
    client_contact_name: str | None = Field(default=None, max_length=200)
    client_contact_email: str | None = Field(default=None, max_length=200)
    client_contact_company: str | None = Field(default=None, max_length=200)


class DecisionRoomItemOverrides(BaseModel):
    """Overrides editables por el consultor para un candidato del room."""

    recommendation: (
        Literal[
            "highly_recommended",
            "recommended",
            "recommended_with_validations",
            "reserve",
            "not_recommended",
        ]
        | None
    ) = None
    consultant_summary: str | None = Field(default=None, max_length=2000)
    why_fits: list[str] | None = Field(default=None, max_length=10)
    risks_or_validations: list[str] | None = Field(default=None, max_length=10)
    evidence_level: Literal["high", "medium", "low"] | None = None
    availability: str | None = Field(default=None, max_length=200)
    salary_expectation: str | None = Field(default=None, max_length=200)
    salary_share_authorized: bool | None = None


class DecisionRoomReorderPayload(BaseModel):
    ordered_item_ids: list[int] = Field(..., min_length=1)


class DecisionRoomPinPayload(BaseModel):
    pinned: bool


class DecisionRoomAddItemPayload(BaseModel):
    evaluation_id: int


class DecisionRoomCloseResponse(BaseModel):
    id: int
    status: str
    closed_at: datetime | None


# --- Access code ------------------------------------------------------------


class AccessCodeIssuePayload(BaseModel):
    # 24h, 3d, 7d, 14d o 30d. 7d (168h) por defecto según spec §6.
    ttl_hours: Literal[24, 72, 168, 336, 720] = 168


class AccessCodeIssueResponse(BaseModel):
    """Devuelve el código en claro una sola vez. No se vuelve a exponer."""

    code: str
    code_expires_at: datetime
    access_expires_at: datetime | None


class AccessCodeValidatePayload(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)

    @field_validator("code")
    @classmethod
    def _digits_only(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("El código debe ser de 6 dígitos numéricos.")
        return value


class AccessCodeValidateResponse(BaseModel):
    session_token: str
    session_expires_at: datetime


class RegenerateAccessResponse(BaseModel):
    public_token: str
    code: str
    code_expires_at: datetime


# --- Items / shortlist read -------------------------------------------------


class ClientShortlistItemRead(BaseModel):
    id: int
    shortlist_id: int
    candidate_id: int
    evaluation_id: int | None
    order_index: int
    is_pinned: bool
    recommendation: str | None
    consultant_summary: str | None
    why_fits: list[str] = Field(default_factory=list)
    risks_or_validations: list[str] = Field(default_factory=list)
    evidence_level: str | None
    availability: str | None
    salary_expectation: str | None
    salary_share_authorized: bool
    rating: int | None
    client_status: str | None
    client_comment: str | None
    status_updated_at: datetime | None
    created_at: datetime
    # Enriquecido por el router para que el Room Builder consultor no tenga que
    # hacer N+1 calls a /api/candidatos y /api/evaluaciones.
    candidate_name: str | None = None
    candidate_current_position: str | None = None
    candidate_current_company: str | None = None
    candidate_linkedin_url: str | None = None
    evaluation_score: int | None = None
    evaluation_score_category: str | None = None

    model_config = {"from_attributes": True}


class ClientShortlistRead(BaseModel):
    id: int
    mandate_id: int
    public_token: str
    title: str
    message_to_client: str
    intro_message: str | None
    show_scores: bool
    show_availability: bool
    show_salary: bool
    show_risks: bool
    show_comparison: bool
    allow_comments: bool
    allow_rating: bool
    allow_report_download: bool
    access_code_required: bool
    access_code_expires_at: datetime | None
    expires_at: datetime | None
    revoked: bool
    status: str
    client_contact_name: str | None
    client_contact_email: str | None
    client_contact_company: str | None
    last_invitation_sent_at: datetime | None
    viewed_at: datetime | None
    viewed_count: int
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[ClientShortlistItemRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# --- Events -----------------------------------------------------------------


class DecisionRoomEventRead(BaseModel):
    id: int
    shortlist_id: int
    item_id: int | None
    event_type: str
    event_label: str
    actor_type: str
    actor_name: str | None
    actor_email: str | None
    event_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Public payloads --------------------------------------------------------


class PublicShortlistCandidate(BaseModel):
    """Vista sanitizada para el cliente final.

    No incluye scores internos, brechas crudas ni notas internas. Cada campo
    sensible se respeta contra los toggles del room.
    """

    item_id: int
    candidate_id: int
    full_name: str
    current_position: str | None
    current_company: str | None
    country: str | None
    linkedin_url: str | None
    total_years_experience: int | None
    inferred_seniority: str | None
    headline: str
    professional_summary: str
    strengths: list[str] = Field(default_factory=list)
    transferable_skills: list[str] = Field(default_factory=list)
    career_trajectory: dict[str, Any] = Field(default_factory=dict)
    education: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    areas_to_validate: list[str] = Field(default_factory=list)
    why_fits: list[str] = Field(default_factory=list)
    risks_or_validations: list[str] = Field(default_factory=list)
    # Vista premium
    experience: list[dict[str, Any]] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    dimension_scores: list[dict[str, Any]] = Field(default_factory=list)
    interview_questions: list[str] = Field(default_factory=list)
    final_verdict: str | None = None
    has_report: bool = False
    can_download_report: bool = False
    consultant_summary: str | None = None
    recommendation: str | None = None
    evidence_level: str | None = None
    availability: str | None = None
    salary_expectation: str | None = None
    is_pinned: bool = False
    order_index: int = 0
    score: int | None = None
    score_category: str | None = None
    client_status: str | None = None
    client_comment: str | None = None
    rating: int | None = None


class PublicShortlistView(BaseModel):
    title: str
    message_to_client: str
    intro_message: str | None
    expires_at: datetime | None
    revoked: bool
    status: str
    show_scores: bool
    show_availability: bool
    show_salary: bool
    show_risks: bool
    show_comparison: bool
    allow_comments: bool
    allow_rating: bool
    allow_report_download: bool
    mandate: dict[str, Any]
    candidates: list[PublicShortlistCandidate]
    created_at: datetime


class PublicShortlistGateView(BaseModel):
    """Vista mínima cuando el room exige código y aún no se validó."""

    requires_code: Literal[True] = True
    title: str
    mandate: dict[str, Any]
    expires_at: datetime | None
    client_contact_email_hint: str | None = None  # ej. "f***@tooxs.com"


class PublicFeedbackPayload(BaseModel):
    client_status: (
        Literal[
            # Históricos
            "interested",
            "not_interested",
            "want_interview",
            # Decision Room
            "favorite",
            "interview_requested",
            "more_info_requested",
            "keep_in_review",
            "rejected",
        ]
        | None
    ) = None
    client_comment: str | None = Field(default=None, max_length=2000)
    rating: int | None = Field(default=None, ge=1, le=5)
