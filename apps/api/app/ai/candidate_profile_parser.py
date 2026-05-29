"""Parser de CV → Perfil estructurado del candidato.

Estrategia:
1. Intentar parseo con gpt-4o-mini en JSON mode.
2. Validar la respuesta con Pydantic; si falla, usar fallback determinista (regex/keywords).
3. Siempre enriquecer email/teléfono del candidato vía regex (no requiere IA).

Reglas duras (AGENTS.md §16):
- No inventar información: si algo no está en el CV, marcar "No evidenciado en el CV".
- No inferir datos personales sensibles (edad, género, religión, etc).
"""

from __future__ import annotations

import json
import logging
import re

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.ai.openai_client import generate_structured_json
from app.models.candidate import Candidate
from app.models.candidate_document import CandidateDocument

logger = logging.getLogger(__name__)


YEARS_PATTERN = re.compile(r"(\d{1,2})\s*(?:anos|años|years|yrs)", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"(\+?\d[\d\s\-\(\)]{7,}\d)")

MAX_CV_CHARS_FOR_LLM = 16000


def _coerce_str_list(value: object) -> list[str]:
    """La IA a veces devuelve un string en lugar de lista. Coercionamos."""
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value)]


class _RoleOut(BaseModel):
    title: str = ""
    company: str = ""
    start_date: str = ""
    end_date: str = ""
    duration_years: float = 0
    responsibilities: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    tools_or_systems: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)

    @field_validator(
        "responsibilities",
        "achievements",
        "tools_or_systems",
        "evidence",
        mode="before",
    )
    @classmethod
    def _coerce_list(cls, value: object) -> list[str]:
        return _coerce_str_list(value)


class _CandidateProfileLLMOutput(BaseModel):
    current_position: str | None = None
    current_company: str | None = None
    total_years_experience: int | None = None
    industries: list[str] = Field(default_factory=list)
    roles: list[_RoleOut] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    inferred_seniority: str | None = None
    missing_information: list[str] = Field(default_factory=list)
    evidence_snippets: list[str] = Field(default_factory=list)

    @field_validator(
        "industries",
        "education",
        "certifications",
        "tools",
        "languages",
        "achievements",
        "missing_information",
        "evidence_snippets",
        mode="before",
    )
    @classmethod
    def _coerce_top_lists(cls, value: object) -> list[str]:
        return _coerce_str_list(value)


# --- Fallback determinista ----------------------------------------------------


def _detect_list(lines: list[str], keywords: tuple[str, ...]) -> list[str]:
    results: list[str] = []
    for line in lines:
        lowered = line.lower()
        if any(keyword in lowered for keyword in keywords):
            results.append(line.strip())
    return results[:10]


def _extract_years(text: str) -> int | None:
    years = [int(match.group(1)) for match in YEARS_PATTERN.finditer(text)]
    if not years:
        return None
    return max(years)


def _fallback_parse(candidate: Candidate, document: CandidateDocument) -> dict[str, object]:
    text = (document.raw_text or "").strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    industries_keywords = (
        "retail",
        "finanzas",
        "tecnologia",
        "tecnología",
        "salud",
        "mineria",
        "minería",
        "logistica",
        "logística",
        "banca",
        "consumo masivo",
        "energia",
        "energía",
    )
    tools_keywords = ("sap", "salesforce", "power bi", "excel", "crm", "sql", "python", "tableau", "hubspot")
    cert_keywords = ("certificacion", "certificación", "certified", "pmp", "scrum", "aws", "itil", "iso")
    education_keywords = ("universidad", "ingenier", "licenci", "magister", "magíster", "mba", "master")
    language_keywords = ("ingles", "inglés", "english", "portugues", "portugués", "frances", "francés", "german", "italiano")

    industries = _detect_list(lines, industries_keywords)
    tools = _detect_list(lines, tools_keywords)
    certifications = _detect_list(lines, cert_keywords)
    education = _detect_list(lines, education_keywords)
    languages = _detect_list(lines, language_keywords)
    achievements = [
        line
        for line in lines
        if "%" in line or re.search(r"\b(kpi|aumento|reducci[oó]n|crecimiento)\b", line.lower())
    ][:10]

    years = _extract_years(text)
    inferred_seniority = None
    if years is not None:
        if years >= 10:
            inferred_seniority = "Senior"
        elif years >= 5:
            inferred_seniority = "Semi Senior"
        else:
            inferred_seniority = "Intermedio"

    evidence_snippets = lines[:8]

    roles: list[dict[str, object]] = []
    for line in lines:
        if "-" in line and len(roles) < 6:
            parts = [part.strip() for part in line.split("-") if part.strip()]
            if len(parts) >= 2:
                roles.append(
                    {
                        "title": parts[0][:120],
                        "company": parts[1][:120],
                        "start_date": "",
                        "end_date": "",
                        "duration_years": 0,
                        "responsibilities": [],
                        "achievements": [],
                        "tools_or_systems": [],
                        "evidence": [line[:200]],
                    }
                )

    missing_information: list[str] = []
    if not industries:
        missing_information.append("No evidenciado en el CV: industrias objetivo")
    if not achievements:
        missing_information.append("No evidenciado en el CV: logros medibles")
    if years is None:
        missing_information.append("No evidenciado en el CV: años de experiencia total")
    if not languages:
        missing_information.append("No evidenciado en el CV: idiomas")

    return _build_payload(
        candidate=candidate,
        current_position=candidate.current_position,
        current_company=candidate.current_company,
        years=years,
        industries=industries,
        roles=roles,
        education=education,
        certifications=certifications,
        tools=tools,
        languages=languages,
        achievements=achievements,
        inferred_seniority=inferred_seniority,
        missing_information=missing_information,
        evidence_snippets=evidence_snippets,
    )


def _build_payload(
    *,
    candidate: Candidate,
    current_position: str | None,
    current_company: str | None,
    years: int | None,
    industries: list[str],
    roles: list[dict[str, object]],
    education: list[str],
    certifications: list[str],
    tools: list[str],
    languages: list[str],
    achievements: list[str],
    inferred_seniority: str | None,
    missing_information: list[str],
    evidence_snippets: list[str],
) -> dict[str, object]:
    profile_json: dict[str, object] = {
        "candidate_name": candidate.full_name,
        "current_position": current_position,
        "current_company": current_company,
        "total_years_experience": years,
        "industries": industries,
        "roles": roles,
        "education": education,
        "certifications": certifications,
        "tools": tools,
        "languages": languages,
        "achievements": achievements,
        "inferred_seniority": inferred_seniority,
        "missing_information": missing_information,
        "evidence_snippets": evidence_snippets,
    }
    return {
        "current_position": current_position,
        "current_company": current_company,
        "total_years_experience": years,
        "industries": industries,
        "roles": roles,
        "education": education,
        "certifications": certifications,
        "tools": tools,
        "languages": languages,
        "achievements": achievements,
        "inferred_seniority": inferred_seniority,
        "missing_information": missing_information,
        "evidence_snippets": evidence_snippets,
        "parsed_json": profile_json,
    }


# --- LLM path ----------------------------------------------------------------


SYSTEM_PROMPT = """Eres un consultor senior de búsqueda ejecutiva en español, experto en
analizar CVs y extraer perfiles estructurados para evaluación 360.

Reglas duras:
- Responde SIEMPRE en español profesional, sin emojis.
- NO inventes información. Si un dato no aparece en el CV, agrégalo a
  missing_information con el formato "No evidenciado en el CV: <tema>".
- NO infieras edad, género, estado civil, religión, nacionalidad, salud,
  dirección, foto ni situación familiar. Ignora estos campos aunque aparezcan.
- Cita evidencia textual breve del CV cuando puedas en evidence_snippets.
- Devuelve EXCLUSIVAMENTE un objeto JSON válido con las claves especificadas.
"""


def _user_prompt(candidate: Candidate, document: CandidateDocument) -> str:
    raw_text = (document.raw_text or "").strip()
    if len(raw_text) > MAX_CV_CHARS_FOR_LLM:
        raw_text = raw_text[:MAX_CV_CHARS_FOR_LLM] + "\n\n[... CV truncado ...]"
    contact = {
        "nombre": candidate.full_name,
        "email": candidate.email,
        "telefono": candidate.phone,
        "cargo_actual_declarado": candidate.current_position,
        "empresa_actual_declarada": candidate.current_company,
    }
    return (
        "Analiza el siguiente CV y devuelve un perfil estructurado en JSON con estas "
        "claves obligatorias: current_position, current_company, total_years_experience, "
        "industries, roles, education, certifications, tools, languages, achievements, "
        "inferred_seniority, missing_information, evidence_snippets.\n\n"
        "Cada rol en 'roles' debe ser un objeto con: title, company, start_date, end_date, "
        "duration_years (número), responsibilities, achievements, tools_or_systems, evidence.\n\n"
        "inferred_seniority puede ser uno de: 'Trainee', 'Junior', 'Intermedio', 'Semi Senior', "
        "'Senior', 'Lead', 'Director', 'C-Level' o null si no es deducible.\n\n"
        f"Datos de contacto declarados:\n{json.dumps(contact, ensure_ascii=False, indent=2)}\n\n"
        f"Texto del CV:\n---\n{raw_text}\n---"
    )


def _llm_to_payload(
    llm_data: _CandidateProfileLLMOutput, candidate: Candidate
) -> dict[str, object]:
    roles = [role.model_dump() for role in llm_data.roles]
    return _build_payload(
        candidate=candidate,
        current_position=llm_data.current_position or candidate.current_position,
        current_company=llm_data.current_company or candidate.current_company,
        years=llm_data.total_years_experience,
        industries=llm_data.industries,
        roles=roles,
        education=llm_data.education,
        certifications=llm_data.certifications,
        tools=llm_data.tools,
        languages=llm_data.languages,
        achievements=llm_data.achievements,
        inferred_seniority=llm_data.inferred_seniority,
        missing_information=llm_data.missing_information,
        evidence_snippets=llm_data.evidence_snippets,
    )


def parse_candidate_profile(candidate: Candidate, document: CandidateDocument) -> dict[str, object]:
    raw_text = (document.raw_text or "").strip()
    if not raw_text:
        return _fallback_parse(candidate, document)

    raw = generate_structured_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=_user_prompt(candidate, document),
        purpose="candidate_profile",
        temperature=0.1,
    )
    if raw is None:
        return _fallback_parse(candidate, document)
    try:
        llm_data = _CandidateProfileLLMOutput.model_validate(raw)
    except ValidationError as exc:
        logger.warning("Candidate profile LLM output inválido (%s); usando fallback.", exc)
        return _fallback_parse(candidate, document)
    return _llm_to_payload(llm_data, candidate)


def enrich_candidate_contact(candidate: Candidate, raw_text: str) -> None:
    if not candidate.email:
        email_match = EMAIL_PATTERN.search(raw_text)
        if email_match:
            candidate.email = email_match.group(0)

    if not candidate.phone:
        phone_match = PHONE_PATTERN.search(raw_text)
        if phone_match:
            candidate.phone = phone_match.group(0)
