from datetime import datetime

from pydantic import BaseModel, Field


class RegisterPayload(BaseModel):
    email: str = Field(..., max_length=200)
    password: str = Field(..., min_length=8, max_length=200)
    full_name: str | None = Field(default=None, max_length=200)


class LoginPayload(BaseModel):
    email: str = Field(..., max_length=200)
    password: str = Field(..., max_length=200)


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: str
    organization_id: int | None
    email_verified: bool
    oauth_provider: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrganizationRead(BaseModel):
    id: int
    name: str
    primary_domain: str | None
    plan: str

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    token: str
    user: UserRead
    organization: OrganizationRead | None
