from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PositionSpecBase(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    executive_summary: str = ""
    role_mission: str = ""
    search_context: str = ""
    key_responsibilities: list[str] = Field(default_factory=list)
    expected_results: list[str] = Field(default_factory=list)
    must_have_requirements: list[dict[str, Any]] = Field(default_factory=list)
    nice_to_have_requirements: list[dict[str, Any]] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    functional_skills: list[str] = Field(default_factory=list)
    leadership_skills: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)
    target_company_types: list[str] = Field(default_factory=list)
    equivalent_roles: list[str] = Field(default_factory=list)
    market_mapping_hypothesis: str = ""
    evaluation_criteria: list[str] = Field(default_factory=list)
    interview_questions: list[str] = Field(default_factory=list)
    scoring_model: list[dict[str, Any]] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    validation_questions: list[str] = Field(default_factory=list)
    generated_by_model: str = "talenscan-rules-v1"
    prompt_version: str = "position-spec-v1"


class PositionSpecCreate(PositionSpecBase):
    search_mandate_id: int


class PositionSpecUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    executive_summary: str | None = None
    role_mission: str | None = None
    search_context: str | None = None
    key_responsibilities: list[str] | None = None
    expected_results: list[str] | None = None
    must_have_requirements: list[dict[str, Any]] | None = None
    nice_to_have_requirements: list[dict[str, Any]] | None = None
    technical_skills: list[str] | None = None
    functional_skills: list[str] | None = None
    leadership_skills: list[str] | None = None
    target_industries: list[str] | None = None
    target_company_types: list[str] | None = None
    equivalent_roles: list[str] | None = None
    market_mapping_hypothesis: str | None = None
    evaluation_criteria: list[str] | None = None
    interview_questions: list[str] | None = None
    scoring_model: list[dict[str, Any]] | None = None
    red_flags: list[str] | None = None
    validation_questions: list[str] | None = None
    generated_by_model: str | None = None
    prompt_version: str | None = None


class PositionSpecRead(PositionSpecBase):
    id: int
    search_mandate_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
