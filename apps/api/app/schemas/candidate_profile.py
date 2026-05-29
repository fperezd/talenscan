from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CandidateProfileRead(BaseModel):
    id: int
    candidate_id: int
    candidate_document_id: int | None = None
    current_position: str | None
    current_company: str | None
    total_years_experience: int | None
    industries: list[str] = Field(default_factory=list)
    roles: list[dict[str, Any]] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    inferred_seniority: str | None
    missing_information: list[str] = Field(default_factory=list)
    evidence_snippets: list[str] = Field(default_factory=list)
    parsed_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}
