from datetime import datetime

from pydantic import BaseModel, Field


class CandidateBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    email: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=80)
    linkedin_url: str | None = Field(default=None, max_length=400)
    current_position: str | None = Field(default=None, max_length=200)
    current_company: str | None = Field(default=None, max_length=200)
    country: str | None = Field(default=None, max_length=120)


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    email: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=80)
    linkedin_url: str | None = Field(default=None, max_length=400)
    current_position: str | None = Field(default=None, max_length=200)
    current_company: str | None = Field(default=None, max_length=200)
    country: str | None = Field(default=None, max_length=120)


class CandidateRead(CandidateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
