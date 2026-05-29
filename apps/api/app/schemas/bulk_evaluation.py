from typing import Literal

from pydantic import BaseModel


class BulkEvaluationItem(BaseModel):
    file_name: str
    status: Literal["created", "duplicate", "error"]
    candidate_id: int | None = None
    candidate_name: str | None = None
    evaluation_id: int | None = None
    pipeline_item_id: int | None = None
    error: str | None = None


class BulkEvaluationResponse(BaseModel):
    items: list[BulkEvaluationItem]
    total: int
    created_count: int
    duplicate_count: int
    error_count: int


class LinkedInEntry(BaseModel):
    url: str
    profile_text: str | None = None


class BulkLinkedInRequest(BaseModel):
    urls_text: str | None = None
    entries: list[LinkedInEntry] | None = None
    position_spec_id: int | None = None  # si se entrega, genera Evaluación 360


class BulkLinkedInItem(BaseModel):
    url: str
    status: Literal["created", "duplicate", "error"]
    candidate_id: int | None = None
    candidate_name: str | None = None
    pipeline_item_id: int | None = None
    error: str | None = None


class BulkLinkedInResponse(BaseModel):
    items: list[BulkLinkedInItem]
    total: int
    created_count: int
    duplicate_count: int
    error_count: int
