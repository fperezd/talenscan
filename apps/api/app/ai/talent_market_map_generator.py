"""Generador del Talent Market Map.

Estrategia:
1. Intentar con gpt-4o-mini en JSON mode.
2. Validar la respuesta con Pydantic; si falla, fallback determinista desde
   el PositionSpec (que ya tiene target_industries, target_companies y
   equivalent_roles).
3. Persistimos `generated_by_model` y `prompt_version` para auditoría.

El output del generador es un diccionario con la "receta" del mapa
(executive_summary + segments + companies + equivalent_roles).
El servicio caller decide cómo persistir (crear/actualizar entidades).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from app.ai.openai_client import generate_structured_json
from app.core.config import settings
from app.models.position_spec import PositionSpec
from app.models.search_mandate import SearchMandate

logger = logging.getLogger(__name__)


PROMPT_VERSION = "talent-market-map-v1"
FALLBACK_PROMPT_VERSION = "talent-market-map-fallback-v1"


# --- Schema de salida esperada ----------------------------------------------


class _SegmentOut(BaseModel):
    name: str
    segment_type: Literal["primary", "adjacent", "exploratory"]
    description: str | None = None
    priority: Literal["high", "medium", "low"] = "medium"
    rationale: str | None = None


class _CompanyOut(BaseModel):
    name: str
    industry: str | None = None
    segment_name: str | None = None  # se resuelve al ID en el service caller
    priority: Literal["high", "medium", "low"] = "medium"
    rationale: str | None = None


class _EquivalentRoleOut(BaseModel):
    title: str
    seniority: str | None = None
    closeness: Literal["high", "medium", "low"] = "medium"
    priority: Literal["high", "medium", "low"] = "medium"
    industries: list[str] = Field(default_factory=list)
    rationale: str | None = None


class _MapLLMOutput(BaseModel):
    executive_summary: str
    market_assessment: Literal["broad", "moderate", "narrow", "very_narrow"] = "moderate"
    segments: list[_SegmentOut] = Field(default_factory=list)
    companies: list[_CompanyOut] = Field(default_factory=list)
    equivalent_roles: list[_EquivalentRoleOut] = Field(default_factory=list)


# --- Prompt -----------------------------------------------------------------


_SYSTEM_PROMPT = """Eres un consultor experto en búsqueda ejecutiva (executive search) en LATAM.
Tu rol es analizar un mandato de búsqueda y su perfil objetivo, y producir un
mapa estratégico del mercado de talento en español profesional.

Reglas estrictas:
- NO inventes empresas que no existan o que sean improbables en el mercado del cargo.
- Basate ÚNICAMENTE en el mandato y perfil objetivo provistos. No inventes datos.
- Si no tienes información suficiente para algún campo, deja la lista vacía.
- Toda la respuesta debe ser un JSON válido (sin texto adicional).
- Las descripciones y rationales deben ser concisas (2-3 oraciones).
- El resumen ejecutivo debe ser accionable y ejecutivo (200-400 palabras).
- Devuelve hasta 6 segmentos, 15 empresas y 10 cargos equivalentes.
- Los segmentos deben clasificarse:
  - "primary": mismo sector / competidores directos
  - "adjacent": industrias con perfiles transferibles
  - "exploratory": segmentos menos obvios pero potencialmente útiles
- Para cada empresa, "segment_name" debe coincidir EXACTAMENTE con el "name"
  de alguno de los segmentos que devolviste."""


_OUTPUT_SCHEMA_HINT = """Schema esperado:
{
  "executive_summary": "string (200-400 palabras, accionable)",
  "market_assessment": "broad" | "moderate" | "narrow" | "very_narrow",
  "segments": [
    {
      "name": "string",
      "segment_type": "primary" | "adjacent" | "exploratory",
      "description": "string corto",
      "priority": "high" | "medium" | "low",
      "rationale": "string corto"
    }
  ],
  "companies": [
    {
      "name": "string (empresa real)",
      "industry": "string",
      "segment_name": "string (debe coincidir con un segments[].name)",
      "priority": "high" | "medium" | "low",
      "rationale": "string corto"
    }
  ],
  "equivalent_roles": [
    {
      "title": "string",
      "seniority": "string opcional",
      "closeness": "high" | "medium" | "low",
      "priority": "high" | "medium" | "low",
      "industries": ["string"],
      "rationale": "string corto"
    }
  ]
}"""


def _build_user_prompt(mandate: SearchMandate, spec: PositionSpec | None) -> str:
    sections: list[str] = []
    sections.append(f"## Mandato\nCliente: {mandate.client_name}")
    sections.append(f"Cargo objetivo: {mandate.target_role}")
    if mandate.industry:
        sections.append(f"Industria del cliente: {mandate.industry}")
    if mandate.country:
        sections.append(f"País: {mandate.country}")
    if mandate.city:
        sections.append(f"Ciudad: {mandate.city}")
    if mandate.seniority_level:
        sections.append(f"Seniority: {mandate.seniority_level}")
    if mandate.business_context:
        sections.append(f"Contexto: {mandate.business_context}")
    if mandate.role_objective:
        sections.append(f"Objetivo del rol: {mandate.role_objective}")
    if mandate.target_companies:
        sections.append(
            f"Empresas sugeridas en mandato: {', '.join(mandate.target_companies)}"
        )
    if mandate.target_industries:
        sections.append(
            f"Industrias sugeridas en mandato: {', '.join(mandate.target_industries)}"
        )
    if mandate.equivalent_roles:
        sections.append(
            f"Cargos equivalentes sugeridos en mandato: {', '.join(mandate.equivalent_roles)}"
        )

    if spec is not None:
        sections.append("\n## Perfil objetivo del cargo")
        if spec.executive_summary:
            sections.append(f"Resumen: {spec.executive_summary}")
        if spec.role_mission:
            sections.append(f"Misión: {spec.role_mission}")
        if spec.target_industries:
            sections.append(f"Industrias objetivo: {', '.join(spec.target_industries)}")
        if spec.target_company_types:
            sections.append(
                f"Tipos de empresa objetivo: {', '.join(spec.target_company_types)}"
            )
        if spec.equivalent_roles:
            sections.append(f"Cargos equivalentes: {', '.join(spec.equivalent_roles)}")
        if spec.market_mapping_hypothesis:
            sections.append(
                f"Hipótesis de mercado: {spec.market_mapping_hypothesis}"
            )
        if spec.must_have_requirements:
            try:
                must_haves = [
                    r.get("requisito", "") if isinstance(r, dict) else str(r)
                    for r in spec.must_have_requirements
                ]
                sections.append(
                    f"Requisitos excluyentes: {', '.join(filter(None, must_haves))}"
                )
            except Exception:  # noqa: BLE001
                pass

    sections.append(f"\n{_OUTPUT_SCHEMA_HINT}")
    sections.append(
        "\nGenera el mapa de mercado. Recuerda: JSON puro, sin texto adicional."
    )
    return "\n".join(sections)


# --- Fallback determinista --------------------------------------------------


def _fallback_from_spec(
    mandate: SearchMandate, spec: PositionSpec | None
) -> dict[str, Any]:
    """Construye un mapa básico usando sólo los datos estructurados del PositionSpec."""
    summary_pieces = [
        f"Mapa de mercado inicial para {mandate.target_role} en {mandate.client_name}."
    ]
    if mandate.industry:
        summary_pieces.append(
            f"El cargo se sitúa en la industria {mandate.industry}."
        )
    if spec and spec.target_industries:
        summary_pieces.append(
            "Industrias objetivo identificadas: "
            + ", ".join(list(spec.target_industries)[:5])
            + "."
        )
    summary_pieces.append(
        "Este mapa fue generado de forma determinista a partir del mandato y "
        "perfil objetivo. La calidad mejorará cuando se cuente con OpenAI "
        "habilitado o cuando se carguen y evalúen más candidatos."
    )
    executive_summary = " ".join(summary_pieces)

    segments: list[dict[str, Any]] = []
    if spec and spec.target_industries:
        primary_ind = list(spec.target_industries)[0]
        segments.append(
            {
                "name": f"Mercado principal: {primary_ind}",
                "segment_type": "primary",
                "description": f"Empresas del sector {primary_ind} directamente relacionadas con el perfil.",
                "priority": "high",
                "rationale": "Sector directo del cargo según mandato.",
            }
        )
        for ind in list(spec.target_industries)[1:4]:
            segments.append(
                {
                    "name": f"Mercado adyacente: {ind}",
                    "segment_type": "adjacent",
                    "description": f"Industria con perfiles transferibles desde {ind}.",
                    "priority": "medium",
                    "rationale": "Sector sugerido en el perfil objetivo.",
                }
            )
    if not segments:
        # Sin información de industrias, segmento genérico
        segments.append(
            {
                "name": "Mercado principal",
                "segment_type": "primary",
                "description": "Empresas directamente relacionadas con el cargo objetivo.",
                "priority": "high",
                "rationale": "Segmento por defecto. Edita manualmente o ejecuta generación IA.",
            }
        )

    companies: list[dict[str, Any]] = []
    source_companies = (
        list(mandate.target_companies or [])
        + (
            list(spec.target_company_types) if spec and spec.target_company_types else []
        )
    )
    seen: set[str] = set()
    for raw in source_companies:
        if not raw:
            continue
        text = raw.strip()
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        companies.append(
            {
                "name": text,
                "industry": mandate.industry,
                "segment_name": segments[0]["name"],
                "priority": "medium",
                "rationale": "Empresa sugerida en el mandato/perfil objetivo.",
            }
        )

    equivalent_roles: list[dict[str, Any]] = []
    role_sources = list(spec.equivalent_roles) if spec and spec.equivalent_roles else []
    role_sources += list(mandate.equivalent_roles or [])
    seen_roles: set[str] = set()
    for raw in role_sources:
        if not raw:
            continue
        text = raw.strip()
        key = text.casefold()
        if key in seen_roles:
            continue
        seen_roles.add(key)
        equivalent_roles.append(
            {
                "title": text,
                "seniority": mandate.seniority_level,
                "closeness": "medium",
                "priority": "medium",
                "industries": list(spec.target_industries[:3]) if spec else [],
                "rationale": "Cargo equivalente sugerido en el perfil objetivo.",
            }
        )

    return {
        "executive_summary": executive_summary,
        "market_assessment": "moderate",
        "segments": segments,
        "companies": companies,
        "equivalent_roles": equivalent_roles,
        "_meta": {
            "generated_by_model": "rules-fallback",
            "prompt_version": FALLBACK_PROMPT_VERSION,
        },
    }


# --- Entrada principal ------------------------------------------------------


def generate_talent_market_map(
    mandate: SearchMandate, spec: PositionSpec | None
) -> dict[str, Any]:
    """Devuelve un dict listo para persistir como TalentMarketMap.

    Garantiza siempre devolver algo (fallback si OpenAI falla).
    """
    user_prompt = _build_user_prompt(mandate, spec)
    raw = generate_structured_json(
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        purpose="talent_market_map",
    )

    if raw is not None:
        try:
            parsed = _MapLLMOutput.model_validate(raw)
            payload = parsed.model_dump()
            payload["_meta"] = {
                "generated_by_model": settings.openai_model,
                "prompt_version": PROMPT_VERSION,
            }
            return payload
        except ValidationError as exc:
            logger.warning(
                "talent_market_map LLM output inválido: %s; usando fallback.", exc
            )

    return _fallback_from_spec(mandate, spec)
