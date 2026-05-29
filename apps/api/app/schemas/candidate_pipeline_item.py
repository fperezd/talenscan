from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

PipelineStage = Literal[
    "received",
    "analyzing",
    "evaluated",
    "preselected",
    "interview",
    "reserve",
    "discarded",
    "present_to_client",
]


class CandidatePipelineItemCreate(BaseModel):
    candidate_id: int
    evaluation_id: int | None = None
    stage: PipelineStage = "received"
    tags: list[str] = Field(default_factory=list)
    is_priority: bool = False
    is_shortlisted: bool = False
    consultant_notes: str = ""


class CandidatePipelineItemUpdate(BaseModel):
    stage: PipelineStage | None = None
    stage_order: int | None = None
    is_priority: bool | None = None
    is_shortlisted: bool | None = None
    consultant_notes: str | None = None
    discard_reason: str | None = None
    tags: list[str] | None = None


class CandidatePipelineItemRead(BaseModel):
    id: int
    mandate_id: int
    candidate_id: int
    evaluation_id: int | None
    stage: PipelineStage
    stage_order: int
    is_priority: bool
    is_shortlisted: bool
    consultant_notes: str
    discard_reason: str
    tags: list[str] = Field(default_factory=list)
    last_moved_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PipelineReorderItem(BaseModel):
    id: int
    stage: PipelineStage
    stage_order: int


class PipelineReorderPayload(BaseModel):
    items: list[PipelineReorderItem]
