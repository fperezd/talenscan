from datetime import datetime

from pydantic import BaseModel, Field


class CandidateDocumentRead(BaseModel):
    id: int
    candidate_id: int
    file_name: str
    file_type: str
    file_size: int = Field(ge=0)
    file_url: str | None
    raw_text: str | None
    text_extraction_status: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}
