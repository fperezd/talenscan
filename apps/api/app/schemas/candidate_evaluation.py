from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CandidateEvaluationCreate(BaseModel):
    candidate_id: int
    position_spec_id: int


class CandidateEvaluationRead(BaseModel):
    id: int
    candidate_id: int
    position_spec_id: int
    total_score: int = Field(ge=0, le=100)
    score_category: str
    recommendation: str
    executive_summary: str
    dimension_scores: list[dict[str, Any]] = Field(default_factory=list)
    critical_gaps: list[dict[str, str]] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    interview_questions: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    final_verdict: str
    evaluation_json: dict[str, Any] = Field(default_factory=dict)
    model_version: str
    prompt_version: str
    created_at: datetime

    model_config = {"from_attributes": True}
