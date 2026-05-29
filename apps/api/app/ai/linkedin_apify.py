"""Cliente para enriquecer perfiles LinkedIn vía Apify.

Apify (https://apify.com) ofrece actores pay-per-use para scraping. Reemplaza
a Scrapingdog (que requería plan mensual de $40). Pricing típico:
- $5/mes en créditos free incluidos
- Después ~$0.005-0.010 por perfil según actor

Configurar en Fly:
  fly secrets set APIFY_TOKEN=<token> -a talenscan-api
  fly secrets set APIFY_LINKEDIN_ACTOR=<actor_id_or_slug> -a talenscan-api  # opcional, default: dev_fusion~Linkedin-Profile-Scraper
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


APIFY_BASE_URL = "https://api.apify.com/v2"


def _normalize_actor(actor: str) -> str:
    """Apify acepta tanto 'slug/name' como 'slug~name' en la URL."""
    return actor.replace("/", "~")


def fetch_linkedin_profile(url: str) -> dict[str, Any] | None:
    """Llama al actor de Apify configurado y retorna el primer item del dataset.

    Usa el endpoint run-sync-get-dataset-items que bloquea hasta tener resultados
    (~10-30s por perfil). Si no hay token, retorna None y el caller usa fallback.
    """
    if not settings.apify_enabled:
        return None

    actor = _normalize_actor(settings.apify_linkedin_actor)
    endpoint = f"{APIFY_BASE_URL}/acts/{actor}/run-sync-get-dataset-items"

    # El input depende del actor. dev_fusion espera profileUrls; curious_coder
    # espera "queries". Enviamos ambos por compatibilidad — el actor ignora los
    # campos que no usa.
    payload = {
        "profileUrls": [url],
        "queries": [url],
        "urls": [url],
        "maxResults": 1,
        "maxItems": 1,
    }

    try:
        response = httpx.post(
            endpoint,
            params={"token": settings.apify_token, "timeout": "120"},
            json=payload,
            timeout=settings.apify_timeout_seconds,
        )
    except httpx.HTTPError as error:
        logger.warning("Apify request falló para %s: %s", url, error)
        return None

    if response.status_code >= 300:
        logger.warning(
            "Apify devolvió %s para %s: %s",
            response.status_code,
            url,
            response.text[:300],
        )
        return None

    try:
        data = response.json()
    except ValueError:
        logger.warning("Apify JSON inválido para %s", url)
        return None

    if not isinstance(data, list) or not data:
        logger.warning("Apify dataset vacío para %s", url)
        return None

    first = data[0] if isinstance(data[0], dict) else None
    # Algunos actors devuelven el error dentro del item (success: false o "error": "...")
    if isinstance(first, dict) and (first.get("error") or first.get("success") is False):
        logger.warning(
            "Apify item con error para %s: %s",
            url,
            str(first.get("error") or first.get("message"))[:200],
        )
        return None
    return first


def _get_str(record: dict[str, Any], *keys: str) -> str | None:
    """Devuelve el primer valor no vacío y limpia espacios."""
    for key in keys:
        value = record.get(key)
        if isinstance(value, str):
            cleaned = re.sub(r"\s+", " ", value).strip()
            if cleaned:
                return cleaned
    return None


_SHORT_MONTHS = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def _coerce_date(value: Any) -> str:
    """Convierte un campo de fecha (string, dict {year,month}, ISO, etc.) a string legible."""
    if value is None:
        return ""
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    if isinstance(value, dict):
        year = value.get("year") or value.get("yyyy")
        month = value.get("month") or value.get("mm")
        try:
            year_int = int(year) if year is not None else None
        except (TypeError, ValueError):
            year_int = None
        try:
            month_int = int(month) if month is not None else None
        except (TypeError, ValueError):
            month_int = None
        if year_int and month_int and 1 <= month_int <= 12:
            return f"{_SHORT_MONTHS[month_int]} {year_int}"
        if year_int:
            return str(year_int)
    return ""


def apify_to_candidate_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Mapea respuesta Apify a campos básicos del modelo Candidate."""
    first = (data.get("firstName") or data.get("first_name") or "").strip()
    last = (data.get("lastName") or data.get("last_name") or "").strip()
    full_name = (
        _get_str(data, "fullName", "full_name", "name") or f"{first} {last}".strip() or "Candidato LinkedIn"
    )

    experiences = data.get("experiences") or data.get("experience") or []
    current_exp = experiences[0] if isinstance(experiences, list) and experiences else {}
    current_position = (
        _get_str(current_exp, "position", "title", "role", "headline")
        or _get_str(data, "headline")
    )
    current_company = (
        _get_str(current_exp, "companyName", "company_name", "company")
        or _get_str(data, "company")
    )

    location = (
        _get_str(data, "addressWithCountry", "location", "city")
        or _get_str(current_exp, "location")
    )
    country = None
    if location:
        parts = [p.strip() for p in location.split(",")]
        if parts:
            country = parts[-1]

    return {
        "full_name": full_name,
        "current_position": current_position,
        "current_company": current_company,
        "country": country,
        "city": _get_str(data, "city"),
        "email": _get_str(data, "email"),
        "phone": _get_str(data, "phone"),
    }


def apify_to_full_profile(data: dict[str, Any]) -> dict[str, Any]:
    """Mapea Apify directamente a campos de CandidateProfile (sin pasar por IA)."""
    experiences = data.get("experiences") or data.get("experience") or []
    if not isinstance(experiences, list):
        experiences = []

    roles: list[dict[str, Any]] = []
    total_years = 0.0
    for exp in experiences[:25]:
        if not isinstance(exp, dict):
            continue
        # harvestapi usa "position"; otros actors usan "title" o "role".
        title = _get_str(exp, "position", "title", "role") or ""
        company = (
            _get_str(exp, "companyName", "company_name", "company")
            or _get_str(exp.get("companyInfo") or {}, "name")
            or ""
        )
        if title and company.startswith(title):
            company = company[len(title):].strip(" -·,;")

        # Fechas: harvestapi devuelve startDate/endDate como dict {year, month} o string.
        # Otros actors usan strings planos o anidados.
        raw_start = (
            exp.get("startDate")
            or exp.get("starts_at")
            or exp.get("start_date")
            or exp.get("startedAt")
            or exp.get("startedOn")
            or exp.get("from")
            or (exp.get("duration") or {}).get("start")
            or (exp.get("timePeriod") or {}).get("startDate")
            or (exp.get("period") or {}).get("start")
        )
        raw_end = (
            exp.get("endDate")
            or exp.get("ends_at")
            or exp.get("end_date")
            or exp.get("endedAt")
            or exp.get("endedOn")
            or exp.get("to")
            or (exp.get("duration") or {}).get("end")
            or (exp.get("timePeriod") or {}).get("endDate")
            or (exp.get("period") or {}).get("end")
        )
        starts = _coerce_date(raw_start)
        ends = _coerce_date(raw_end)

        # Fallback a string de rango "Jan 2023 - Present".
        date_range = _get_str(exp, "dateRange", "dates", "period")
        if not starts and date_range and " - " in date_range:
            parts = date_range.split(" - ", 1)
            starts = parts[0].strip()
            ends = ends or parts[1].strip()

        description = _get_str(exp, "description", "summary", "details") or ""
        location = _get_str(exp, "location", "companyLocation") or ""

        # total_duration o duration string es una pista: "1 yr 5 mos" → 1.4
        total_duration_str = _get_str(exp, "totalDuration", "durationLabel") or _get_str(
            exp.get("duration") or {}, "totalDuration", "label"
        )
        duration = _estimate_years(starts, ends)
        if duration == 0 and total_duration_str:
            duration = _parse_duration_label(total_duration_str)

        total_years += duration
        responsibilities = _split_paragraph(description)
        roles.append(
            {
                "title": title,
                "company": company,
                "start_date": starts,
                "end_date": ends or "Actualidad",
                "duration_years": round(duration, 1),
                "responsibilities": responsibilities,
                "achievements": [],
                "tools_or_systems": [],
                "evidence": [location] if location else [],
            }
        )

    educations_raw = data.get("educations") or data.get("education") or []
    education: list[str] = []
    if isinstance(educations_raw, list):
        for edu in educations_raw[:10]:
            if isinstance(edu, str):
                education.append(edu)
            elif isinstance(edu, dict):
                school = (
                    _get_str(edu, "schoolName", "college_name", "school", "institution") or ""
                )
                degree = _get_str(edu, "degreeName", "college_degree", "degree", "degree_name") or ""
                field = _get_str(edu, "fieldOfStudy", "college_degree_field", "field_of_study") or ""
                duration = (
                    _get_str(edu, "duration", "dates", "college_duration") or ""
                )
                pieces = [piece for piece in [degree, field, school, duration] if piece]
                if pieces:
                    education.append(" · ".join(pieces))

    certifications_raw = (
        data.get("certifications")
        or data.get("licensesAndCertifications")
        or data.get("certification")
        or []
    )
    certifications: list[str] = []
    if isinstance(certifications_raw, list):
        for cert in certifications_raw[:15]:
            if isinstance(cert, str):
                certifications.append(cert)
            elif isinstance(cert, dict):
                name = _get_str(cert, "name", "certification_name", "title") or ""
                authority = (
                    _get_str(cert, "authority", "organization", "issuingOrganization") or ""
                )
                if name and authority:
                    certifications.append(f"{name} ({authority})")
                elif name:
                    certifications.append(name)

    # harvestapi expone topSkills (lista curada) y skills (lista completa).
    skills_sources: list[Any] = []
    for src in (data.get("topSkills"), data.get("skills"), data.get("skill")):
        if isinstance(src, list):
            skills_sources.extend(src)
        elif isinstance(src, str):
            skills_sources.extend(re.split(r"[,;|]", src))
    tools: list[str] = []
    for skill in skills_sources[:80]:
        value = (
            skill.strip()
            if isinstance(skill, str)
            else _get_str(skill, "name", "skill", "title") if isinstance(skill, dict) else None
        )
        if value and value not in tools:
            tools.append(value)
        if len(tools) >= 40:
            break

    languages_raw = data.get("languages") or data.get("language") or []
    languages: list[str] = []
    if isinstance(languages_raw, list):
        for lang in languages_raw[:20]:
            value = (
                lang
                if isinstance(lang, str)
                else _get_str(lang, "name", "language") if isinstance(lang, dict) else None
            )
            if value:
                for piece in re.split(r"[,;|]", value):
                    piece = piece.strip()
                    if piece and piece not in languages:
                        languages.append(piece)

    headline = _get_str(data, "headline", "title") or ""
    summary = _get_str(data, "about", "summary", "description") or ""

    achievements: list[str] = []
    for sentence in re.split(r"(?<=[\.\!])\s+", summary)[:50]:
        sentence = sentence.strip()
        if not sentence:
            continue
        lower = sentence.lower()
        if any(
            keyword in lower
            for keyword in (
                "growth", "led", "drove", "increased", "decreased", "scale",
                "crecimiento", "lideré", "lideró", "implementé", "implementó",
                "logré", "logró", "fundé", "fundó", "expandí", "expandió",
                "%", "millones", "million", "billion"
            )
        ):
            achievements.append(sentence[:300])
        if len(achievements) >= 10:
            break

    industries: list[str] = []
    industry_keywords = {
        "Tecnología": ["tech", "technology", "software", "cloud", "saas", "ai", "data"],
        "Consultoría": ["consult", "advisor", "consulting"],
        "Banca y Finanzas": ["bank", "finan", "investment", "capital"],
        "Retail": ["retail", "consumer", "ecommerce"],
        "Salud": ["health", "pharma", "salud", "medical"],
        "Minería": ["mining", "mineria", "minera"],
        "Educación": ["education", "academic", "university", "school"],
        "Energía": ["energy", "energia", "oil", "gas"],
        "Industrial / Manufactura": ["manufactur", "industrial"],
        "Logística": ["logistics", "logistic", "supply chain"],
        "Telecomunicaciones": ["telecom", "telco"],
    }
    text_for_industry = (
        headline + " " + " ".join(role["title"] + " " + role["company"] for role in roles)
    ).lower()
    for industry, keywords in industry_keywords.items():
        if any(kw in text_for_industry for kw in keywords):
            industries.append(industry)

    inferred_seniority = _infer_seniority(roles[0] if roles else None, total_years)

    evidence_snippets: list[str] = []
    if headline:
        evidence_snippets.append(headline)
    for sentence in re.split(r"(?<=[\.\!])\s+", summary)[:5]:
        sentence = sentence.strip()
        if sentence and len(sentence) > 30:
            evidence_snippets.append(sentence[:250])
            if len(evidence_snippets) >= 6:
                break

    missing: list[str] = []
    if not education:
        missing.append("No evidenciado: detalle de formación académica")
    if not certifications:
        missing.append("No evidenciado: certificaciones formales")
    if total_years == 0:
        missing.append("No evidenciado: años de experiencia con fechas claras")

    current_position = roles[0]["title"] if roles else None
    current_company = roles[0]["company"] if roles else None

    return {
        "current_position": current_position,
        "current_company": current_company,
        "total_years_experience": int(total_years) if total_years else None,
        "industries": industries,
        "roles": roles,
        "education": education,
        "certifications": certifications,
        "tools": tools,
        "languages": languages,
        "achievements": achievements,
        "inferred_seniority": inferred_seniority,
        "missing_information": missing,
        "evidence_snippets": evidence_snippets,
        "parsed_json": {
            "candidate_name": _get_str(data, "fullName", "full_name", "name"),
            "source": "linkedin_apify",
        },
    }


_MONTH_LOOKUP = {
    "jan": 1, "ene": 1, "enero": 1, "january": 1,
    "feb": 2, "febrero": 2, "february": 2,
    "mar": 3, "marzo": 3, "march": 3,
    "abr": 4, "apr": 4, "abril": 4, "april": 4,
    "may": 5, "mayo": 5,
    "jun": 6, "junio": 6, "june": 6,
    "jul": 7, "julio": 7, "july": 7,
    "ago": 8, "aug": 8, "agosto": 8, "august": 8,
    "sep": 9, "sept": 9, "septiembre": 9, "september": 9,
    "oct": 10, "octubre": 10, "october": 10,
    "nov": 11, "noviembre": 11, "november": 11,
    "dic": 12, "dec": 12, "diciembre": 12, "december": 12,
}


def _parse_date(value: str) -> tuple[int | None, int | None]:
    if not value:
        return None, None
    cleaned = value.strip().lower()
    if cleaned in ("actualidad", "present", "current", "presente"):
        now = datetime.utcnow()
        return now.year, now.month
    match = re.match(r"([a-záéíóú]+)\s+(\d{4})", cleaned)
    if match:
        month = _MONTH_LOOKUP.get(match.group(1)[:3], None)
        year = int(match.group(2))
        return year, month
    match = re.match(r"(\d{4})", cleaned)
    if match:
        return int(match.group(1)), None
    return None, None


def _estimate_years(starts: str, ends: str) -> float:
    start_year, start_month = _parse_date(starts)
    end_year, end_month = _parse_date(ends or "")
    if end_year is None and end_month is None:
        now = datetime.utcnow()
        end_year, end_month = now.year, now.month
    if start_year is None:
        return 0
    months = (end_year - start_year) * 12 + ((end_month or 1) - (start_month or 1))
    return max(0.0, months / 12)


def _parse_duration_label(label: str) -> float:
    """Convierte etiquetas tipo "1 yr 5 mos" o "3 años 2 meses" en años (float)."""
    if not label:
        return 0.0
    text = label.lower()
    years = 0.0
    months = 0.0
    # Años: "1 yr", "2 yrs", "3 year", "5 years", "1 año", "2 años"
    year_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:yrs?|years?|años?|año)", text)
    if year_match:
        years = float(year_match.group(1).replace(",", "."))
    # Meses: "5 mo", "5 mos", "5 month", "5 months", "5 mes", "5 meses"
    month_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:mos?|months?|meses|mes)", text)
    if month_match:
        months = float(month_match.group(1).replace(",", "."))
    total = years + months / 12
    if total > 0:
        return total
    # Fallback: número solo, asumir años
    bare = re.search(r"(\d+(?:[.,]\d+)?)", text)
    if bare:
        return float(bare.group(1).replace(",", "."))
    return 0.0


def _split_paragraph(text: str) -> list[str]:
    if not text:
        return []
    lines = re.split(r"[••]|\s*\n\s*[-*]\s*|\n\n", text)
    result: list[str] = []
    for line in lines:
        line = line.strip(" -•*\n\t")
        if len(line) > 20:
            result.append(line[:400])
    if not result and text.strip():
        first = re.split(r"(?<=[\.\!])\s+", text.strip())[0]
        result.append(first[:400])
    return result[:8]


def _infer_seniority(current_role: dict[str, Any] | None, total_years: float) -> str | None:
    title = (current_role or {}).get("title", "").lower() if current_role else ""
    if any(k in title for k in ("ceo", "cfo", "coo", "cmo", "cto", "founder", "president")):
        return "C-Level"
    if any(k in title for k in ("vp ", "vice president", "vicepresidente")):
        return "VP"
    if any(k in title for k in ("director", "head of")):
        return "Director"
    if any(k in title for k in ("manager", "gerente", "lead")):
        return "Manager"
    if total_years >= 10:
        return "Senior"
    if total_years >= 5:
        return "Semi Senior"
    if total_years >= 2:
        return "Intermedio"
    return "Junior"
