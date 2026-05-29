from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

MandateStatus = Literal[
    "Borrador",
    "Activo",
    "Perfil objetivo generado",
    "En evaluación de candidatos",
    "Con shortlist",
    "Cerrado",
    "Archivado",
]


class SearchMandateBase(BaseModel):
    client_name: str = Field(min_length=2, max_length=200)
    search_title: str = Field(min_length=2, max_length=200)
    target_role: str = Field(min_length=2, max_length=150)
    industry: str | None = Field(default=None, max_length=150)
    country: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    work_mode: str | None = Field(default=None, max_length=60)
    seniority_level: str | None = Field(default=None, max_length=80)
    reports_to: str | None = Field(default=None, max_length=150)
    business_context: str | None = None
    role_objective: str | None = None
    key_challenges: str | None = None
    main_responsibilities: list[str] = Field(default_factory=list)
    expected_results: list[str] = Field(default_factory=list)
    must_have_requirements: list[str] = Field(default_factory=list)
    nice_to_have_requirements: list[str] = Field(default_factory=list)
    target_companies: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)
    equivalent_roles: list[str] = Field(default_factory=list)
    compensation_context: str | None = None
    urgency: str | None = Field(default=None, max_length=60)
    target_hire_date: date | None = None
    comments: str | None = None
    status: MandateStatus = "Borrador"


class SearchMandateCreate(SearchMandateBase):
    pass


class SearchMandateUpdate(BaseModel):
    client_name: str | None = Field(default=None, min_length=2, max_length=200)
    search_title: str | None = Field(default=None, min_length=2, max_length=200)
    target_role: str | None = Field(default=None, min_length=2, max_length=150)
    industry: str | None = Field(default=None, max_length=150)
    country: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    work_mode: str | None = Field(default=None, max_length=60)
    seniority_level: str | None = Field(default=None, max_length=80)
    reports_to: str | None = Field(default=None, max_length=150)
    business_context: str | None = None
    role_objective: str | None = None
    key_challenges: str | None = None
    main_responsibilities: list[str] | None = None
    expected_results: list[str] | None = None
    must_have_requirements: list[str] | None = None
    nice_to_have_requirements: list[str] | None = None
    target_companies: list[str] | None = None
    target_industries: list[str] | None = None
    equivalent_roles: list[str] | None = None
    compensation_context: str | None = None
    urgency: str | None = Field(default=None, max_length=60)
    target_hire_date: date | None = None
    comments: str | None = None
    status: MandateStatus | None = None


class SearchMandateRead(SearchMandateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
