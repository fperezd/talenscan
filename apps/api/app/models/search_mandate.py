from datetime import date

from sqlalchemy import JSON, Date, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SearchMandate(Base):
    __tablename__ = "search_mandates"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_name: Mapped[str] = mapped_column(String(200), nullable=False)
    search_title: Mapped[str] = mapped_column(String(200), nullable=False)
    target_role: Mapped[str] = mapped_column(String(150), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(150), nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    work_mode: Mapped[str | None] = mapped_column(String(60), nullable=True)
    seniority_level: Mapped[str | None] = mapped_column(String(80), nullable=True)
    reports_to: Mapped[str | None] = mapped_column(String(150), nullable=True)
    business_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    role_objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_challenges: Mapped[str | None] = mapped_column(Text, nullable=True)
    main_responsibilities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    expected_results: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    must_have_requirements: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    nice_to_have_requirements: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    target_companies: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    target_industries: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    equivalent_roles: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    compensation_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    urgency: Mapped[str | None] = mapped_column(String(60), nullable=True)
    target_hire_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(60), nullable=False, default="Borrador")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
