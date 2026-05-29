"""Generador del Perfil objetivo del cargo.

Estrategia:
1. Intentar generación con gpt-4o-mini en JSON mode.
2. Validar la respuesta con Pydantic; si falla, usar fallback determinista.
3. Fusionar campos cuantitativos (scoring_model fijo) con el output IA.

Persistimos model_version y prompt_version según la regla de AGENTS.md §5.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.ai.openai_client import generate_structured_json
from app.core.config import settings
from app.models.search_mandate import SearchMandate

logger = logging.getLogger(__name__)


PROMPT_VERSION = "position-spec-v2"
FALLBACK_PROMPT_VERSION = "position-spec-v1"


SCORING_MODEL_FIXED = [
    {"dimension": "Requisitos excluyentes", "max_score": 20},
    {"dimension": "Experiencia relevante", "max_score": 15},
    {"dimension": "Calce industria / mercado", "max_score": 10},
    {"dimension": "Seniority y nivel de responsabilidad", "max_score": 10},
    {"dimension": "Competencias técnicas", "max_score": 10},
    {"dimension": "Competencias funcionales", "max_score": 10},
    {"dimension": "Logros e impacto demostrable", "max_score": 10},
    {"dimension": "Formación y certificaciones", "max_score": 5},
    {"dimension": "Trayectoria y estabilidad", "max_score": 5},
    {"dimension": "Riesgos y brechas críticas", "max_score": 5},
]


class _RequirementOut(BaseModel):
    requisito: str
    tipo: str = "excluyente"
    fuente_validacion: str = "cv_y_entrevista"
    peso_evaluacion: int = Field(default=5, ge=1, le=20)
    preguntas_validacion: list[str] = Field(default_factory=list)


class _PositionSpecLLMOutput(BaseModel):
    title: str
    executive_summary: str
    role_mission: str
    search_context: str
    key_responsibilities: list[str] = Field(default_factory=list)
    expected_results: list[str] = Field(default_factory=list)
    must_have_requirements: list[_RequirementOut] = Field(default_factory=list)
    nice_to_have_requirements: list[_RequirementOut] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    functional_skills: list[str] = Field(default_factory=list)
    leadership_skills: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)
    target_company_types: list[str] = Field(default_factory=list)
    equivalent_roles: list[str] = Field(default_factory=list)
    market_mapping_hypothesis: str = ""
    evaluation_criteria: list[str] = Field(default_factory=list)
    interview_questions: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    validation_questions: list[str] = Field(default_factory=list)


# --- Fallback determinista ----------------------------------------------------


def _to_requirement(requirement: str, requirement_type: str, weight: int) -> dict[str, object]:
    return {
        "requisito": requirement,
        "tipo": requirement_type,
        "fuente_validacion": "cv_y_entrevista",
        "peso_evaluacion": weight,
        "preguntas_validacion": [f"Describe evidencia concreta de: {requirement}"],
    }


def _infer_seniority_risk(mandate: SearchMandate) -> str:
    if not mandate.seniority_level:
        return "No se evidenció nivel de seniority objetivo en el mandato."
    return f"Validar seniority {mandate.seniority_level} con casos de impacto real."


def _fallback_payload(mandate: SearchMandate) -> dict[str, object]:
    must_reqs = mandate.must_have_requirements or []
    nice_reqs = mandate.nice_to_have_requirements or []
    responsibilities = mandate.main_responsibilities or []
    results = mandate.expected_results or []

    must_have_requirements = [_to_requirement(item, "excluyente", 8) for item in must_reqs]
    nice_to_have_requirements = [_to_requirement(item, "deseable", 4) for item in nice_reqs]

    technical_skills = [item for item in must_reqs[:4]]
    functional_skills = [item for item in responsibilities[:4]]
    leadership_skills = [item for item in (results[:2] + responsibilities[:2])]
    evaluation_criteria = [
        "Cumplimiento de requisitos excluyentes",
        "Experiencia demostrable en responsabilidades críticas",
        "Logros medibles y consistentes con resultados esperados",
        "Calce de industria y nivel de rol",
    ]
    interview_questions = [
        f"¿Qué resultado tangible lograste en {mandate.target_role} con impacto medible?",
        "¿Qué riesgos anticipas en los primeros 90 días del cargo?",
        *[f"¿Cómo demuestras {item}?" for item in must_reqs[:4]],
    ]
    red_flags = [
        _infer_seniority_risk(mandate),
        "No evidenciado en el CV: experiencias clave del rol objetivo.",
        "Validar continuidad y profundidad de logros en contextos similares.",
    ]

    title = f"Perfil objetivo - {mandate.target_role}"
    search_context = mandate.business_context or "Contexto no informado en el mandato."
    mission = mandate.role_objective or f"Cumplir los objetivos clave del cargo {mandate.target_role}."
    summary = (
        f"Mandato para {mandate.client_name}: {mandate.search_title}. "
        f"Cargo objetivo {mandate.target_role} con foco en resultados y trazabilidad."
    )

    return {
        "title": title,
        "executive_summary": summary,
        "role_mission": mission,
        "search_context": search_context,
        "key_responsibilities": responsibilities,
        "expected_results": results,
        "must_have_requirements": must_have_requirements,
        "nice_to_have_requirements": nice_to_have_requirements,
        "technical_skills": technical_skills,
        "functional_skills": functional_skills,
        "leadership_skills": leadership_skills,
        "target_industries": mandate.target_industries or ([mandate.industry] if mandate.industry else []),
        "target_company_types": mandate.target_companies or [],
        "equivalent_roles": mandate.equivalent_roles or [],
        "market_mapping_hypothesis": (
            "Priorizar talento con experiencia comparable en mercado objetivo y escala similar."
        ),
        "evaluation_criteria": evaluation_criteria,
        "interview_questions": interview_questions,
        "scoring_model": SCORING_MODEL_FIXED,
        "red_flags": red_flags,
        "validation_questions": interview_questions[:5],
        "generated_by_model": "talenscan-rules-v1",
        "prompt_version": FALLBACK_PROMPT_VERSION,
    }


# --- LLM path ----------------------------------------------------------------


SYSTEM_PROMPT = """Eres un consultor senior de búsqueda ejecutiva en español, especialista en
levantamiento de mandatos B2B premium (estándar Qavante). Generas perfiles objetivos
de cargo evaluables, profesionales y trazables.

Reglas duras:
- Responde SIEMPRE en español profesional, ejecutivo y sin emojis.
- NO inventes información no presente en el mandato; si falta algo, omítelo del campo.
- Cada requisito debe ser específico, evaluable y útil para comparar candidatos.
- No uses lenguaje juvenil, ni "la IA cree", ni texto genérico de plantilla.
- Devuelve EXCLUSIVAMENTE un objeto JSON válido con las claves especificadas.
"""


def _mandate_to_prompt_payload(mandate: SearchMandate) -> dict[str, Any]:
    return {
        "cliente": mandate.client_name,
        "titulo_busqueda": mandate.search_title,
        "cargo_objetivo": mandate.target_role,
        "industria": mandate.industry,
        "pais": mandate.country,
        "ciudad": mandate.city,
        "modalidad_trabajo": mandate.work_mode,
        "seniority": mandate.seniority_level,
        "reporta_a": mandate.reports_to,
        "contexto_negocio": mandate.business_context,
        "objetivo_del_rol": mandate.role_objective,
        "desafios_clave": mandate.key_challenges,
        "responsabilidades_principales": mandate.main_responsibilities,
        "resultados_esperados": mandate.expected_results,
        "requisitos_excluyentes": mandate.must_have_requirements,
        "requisitos_deseables": mandate.nice_to_have_requirements,
        "empresas_objetivo": mandate.target_companies,
        "industrias_objetivo": mandate.target_industries,
        "cargos_equivalentes": mandate.equivalent_roles,
        "contexto_compensacion": mandate.compensation_context,
        "urgencia": mandate.urgency,
        "comentarios": mandate.comments,
    }


def _user_prompt(mandate: SearchMandate) -> str:
    payload = _mandate_to_prompt_payload(mandate)
    return (
        "Genera un Perfil objetivo del cargo a partir del siguiente mandato. "
        "Estructura el JSON exactamente con estas claves (todas obligatorias): "
        "title, executive_summary, role_mission, search_context, key_responsibilities, "
        "expected_results, must_have_requirements, nice_to_have_requirements, "
        "technical_skills, functional_skills, leadership_skills, target_industries, "
        "target_company_types, equivalent_roles, market_mapping_hypothesis, "
        "evaluation_criteria, interview_questions, red_flags, validation_questions.\n\n"
        "Cada elemento de must_have_requirements y nice_to_have_requirements debe ser un objeto "
        "{requisito, tipo, fuente_validacion, peso_evaluacion (1-20), preguntas_validacion}.\n\n"
        "Los demás campos de lista son listas de strings.\n\n"
        f"Mandato:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def _merge_llm_with_fallback(
    llm_data: _PositionSpecLLMOutput, mandate: SearchMandate
) -> dict[str, object]:
    fallback = _fallback_payload(mandate)
    must_have = [req.model_dump() for req in llm_data.must_have_requirements]
    nice_to_have = [req.model_dump() for req in llm_data.nice_to_have_requirements]
    return {
        "title": llm_data.title or fallback["title"],
        "executive_summary": llm_data.executive_summary or fallback["executive_summary"],
        "role_mission": llm_data.role_mission or fallback["role_mission"],
        "search_context": llm_data.search_context or fallback["search_context"],
        "key_responsibilities": llm_data.key_responsibilities or fallback["key_responsibilities"],
        "expected_results": llm_data.expected_results or fallback["expected_results"],
        "must_have_requirements": must_have or fallback["must_have_requirements"],
        "nice_to_have_requirements": nice_to_have or fallback["nice_to_have_requirements"],
        "technical_skills": llm_data.technical_skills or fallback["technical_skills"],
        "functional_skills": llm_data.functional_skills or fallback["functional_skills"],
        "leadership_skills": llm_data.leadership_skills or fallback["leadership_skills"],
        "target_industries": llm_data.target_industries or fallback["target_industries"],
        "target_company_types": llm_data.target_company_types or fallback["target_company_types"],
        "equivalent_roles": llm_data.equivalent_roles or fallback["equivalent_roles"],
        "market_mapping_hypothesis": llm_data.market_mapping_hypothesis
        or fallback["market_mapping_hypothesis"],
        "evaluation_criteria": llm_data.evaluation_criteria or fallback["evaluation_criteria"],
        "interview_questions": llm_data.interview_questions or fallback["interview_questions"],
        "scoring_model": SCORING_MODEL_FIXED,
        "red_flags": llm_data.red_flags or fallback["red_flags"],
        "validation_questions": llm_data.validation_questions
        or (llm_data.interview_questions[:5] if llm_data.interview_questions else fallback["validation_questions"]),
        "generated_by_model": settings.openai_model,
        "prompt_version": PROMPT_VERSION,
    }


def generate_position_spec_payload(mandate: SearchMandate) -> dict[str, object]:
    raw = generate_structured_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=_user_prompt(mandate),
        purpose="position_spec",
    )
    if raw is None:
        return _fallback_payload(mandate)
    try:
        llm_data = _PositionSpecLLMOutput.model_validate(raw)
    except ValidationError as exc:
        logger.warning("Position spec LLM output inválido (%s); usando fallback.", exc)
        return _fallback_payload(mandate)
    return _merge_llm_with_fallback(llm_data, mandate)
