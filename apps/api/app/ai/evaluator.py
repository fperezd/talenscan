"""Evaluador 360 con IA — calidad de senior headhunter.

Diseño:
- gpt-4o-mini con JSON mode produce una evaluación rica (fortalezas con
  evidencia, brechas con mitigación, oportunidades / habilidades transferibles,
  trayectoria, tesis de talento, foco de referencias, consideraciones de
  onboarding, preguntas de entrevista priorizadas).
- Pydantic valida el shape y coerciona campos mal formados.
- Si OpenAI no está configurado o falla, el caller cae al evaluador determinista
  enriquecido en `fit_score_engine.py`.

La salida se persiste dentro de `evaluation_json["ai_assessment"]` para no
romper compatibilidad con columnas existentes (strengths/weaknesses/risks como
list[str]). Los campos primarios se derivan del payload IA.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.ai.openai_client import generate_structured_json
from app.models.candidate_profile import CandidateProfile
from app.models.position_spec import PositionSpec

logger = logging.getLogger(__name__)


PROMPT_VERSION = "evaluation-v3-headhunter"
MODEL_TAG = "talenscan-ai-evaluation-v3"


# --- Pydantic schemas ---------------------------------------------------------


def _ensure_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    result.append(cleaned)
            elif isinstance(item, dict):
                # tomamos la clave más obvia
                for key in ("text", "detail", "value", "name", "title"):
                    if key in item and isinstance(item[key], str):
                        cleaned = item[key].strip()
                        if cleaned:
                            result.append(cleaned)
                            break
        return result
    return []


class _DimensionScore(BaseModel):
    dimension: str
    score: int = Field(ge=0, le=20)
    max_score: int = Field(ge=1, le=20)
    status: str = ""
    evidence_level: str = "Media"
    rationale: str = ""
    supporting_evidence: list[str] = Field(default_factory=list)

    @field_validator("supporting_evidence", mode="before")
    @classmethod
    def _coerce_ev(cls, v: Any) -> list[str]:
        return _ensure_str_list(v)


class _StrengthDetailed(BaseModel):
    title: str
    detail: str = ""
    evidence: str = ""


class _GapDetailed(BaseModel):
    requirement: str
    reason: str = ""
    impact: str = ""
    evidence: str = "No evidenciado en el CV"
    mitigation: str = ""


class _OpportunityDetailed(BaseModel):
    title: str
    detail: str = ""
    evidence: str = ""


class _RiskDetailed(BaseModel):
    risk: str
    validation: str = ""


class _InterviewQuestion(BaseModel):
    question: str
    objective: str = ""
    priority: str = "Media"


class _CareerTrajectory(BaseModel):
    tenure_stability: str = ""
    progression: str = ""
    current_phase: str = ""
    narrative: str = ""


class _CulturalFitSignal(BaseModel):
    signal: str
    indicator: str = "Neutral"  # Positive | Neutral | Risk


class _EvaluationLLMOutput(BaseModel):
    total_score: int = Field(ge=0, le=100)
    score_category: str
    recommendation: str
    executive_summary: str
    talent_thesis: str
    final_verdict: str
    differentiation: str = ""
    dimension_scores: list[_DimensionScore] = Field(default_factory=list)
    strengths_detailed: list[_StrengthDetailed] = Field(default_factory=list)
    critical_gaps_detailed: list[_GapDetailed] = Field(default_factory=list)
    opportunities: list[_OpportunityDetailed] = Field(default_factory=list)
    transferable_skills: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    risks_detailed: list[_RiskDetailed] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    career_trajectory: _CareerTrajectory = Field(default_factory=_CareerTrajectory)
    cultural_fit_signals: list[_CulturalFitSignal] = Field(default_factory=list)
    interview_questions_detailed: list[_InterviewQuestion] = Field(default_factory=list)
    reference_check_focus: list[str] = Field(default_factory=list)
    onboarding_considerations: list[str] = Field(default_factory=list)
    compensation_signals: str = ""
    supporting_evidence: list[str] = Field(default_factory=list)

    @field_validator("transferable_skills", "weaknesses", "red_flags",
                     "reference_check_focus", "onboarding_considerations",
                     "supporting_evidence", mode="before")
    @classmethod
    def _coerce_list(cls, v: Any) -> list[str]:
        return _ensure_str_list(v)


# --- Prompt construction ------------------------------------------------------


def _profile_block(profile: CandidateProfile) -> dict[str, Any]:
    return {
        "candidate_name": profile.parsed_json.get("candidate_name") if profile.parsed_json else None,
        "current_position": profile.current_position,
        "current_company": profile.current_company,
        "total_years_experience": profile.total_years_experience,
        "inferred_seniority": profile.inferred_seniority,
        "industries": profile.industries or [],
        "roles": profile.roles or [],
        "education": profile.education or [],
        "certifications": profile.certifications or [],
        "tools": profile.tools or [],
        "languages": profile.languages or [],
        "achievements": profile.achievements or [],
        "evidence_snippets": profile.evidence_snippets or [],
        "missing_information": profile.missing_information or [],
    }


def _spec_block(spec: PositionSpec) -> dict[str, Any]:
    return {
        "title": spec.title,
        "executive_summary": spec.executive_summary,
        "role_mission": spec.role_mission,
        "search_context": spec.search_context,
        "key_responsibilities": spec.key_responsibilities or [],
        "expected_results": spec.expected_results or [],
        "must_have_requirements": spec.must_have_requirements or [],
        "nice_to_have_requirements": spec.nice_to_have_requirements or [],
        "technical_skills": spec.technical_skills or [],
        "functional_skills": spec.functional_skills or [],
        "leadership_skills": spec.leadership_skills or [],
        "target_industries": spec.target_industries or [],
        "target_company_types": spec.target_company_types or [],
        "equivalent_roles": spec.equivalent_roles or [],
        "evaluation_criteria": spec.evaluation_criteria or [],
        "red_flags": spec.red_flags or [],
        "scoring_model": spec.scoring_model or [],
    }


SYSTEM_PROMPT = """Eres un Headhunter Senior de búsqueda ejecutiva con 20+ años de experiencia colocando ejecutivos en mandatos C-Level, Director y VP en Latinoamérica. Tu firma cobra retainer y tu reputación depende de la calidad de tus informes de evaluación 360.

Tu tarea: evaluar UN candidato contra UN perfil objetivo (job spec). El output debe ser un JSON estructurado que un Partner senior pueda leer en 5 minutos y tomar una decisión informada.

Reglas de criterio profesional:

1. NUNCA descartes a un candidato solo por falta de industria. Si tiene 30 años liderando equipos en otra industria y la posición pide 10 en la industria objetivo, ESCRIBE EXPLÍCITAMENTE que la brecha de industria es compensable con liderazgo transferible — y agrégalo como "opportunity", no solo como "gap".

2. Distingue siempre entre:
   - "critical_gaps" (brechas que bloquean: ej. requisito legal de idioma, certificación regulatoria, residencia)
   - "weaknesses" (debilidades manejables: industria adyacente, herramientas distintas pero conceptualmente equivalentes)
   - "opportunities" (fortalezas transferibles que el cliente puede no haber valorado: liderazgo cross-industry, gestión de crisis, transformación digital, redes ejecutivas)

3. Para cada brecha y cada riesgo, escribe una "mitigation" o "validation": qué pregunta hacer en entrevista, qué referencia validar, qué documento pedir.

4. La "talent_thesis" es la hipótesis de inversión: en 2-3 oraciones, ¿por qué este candidato puede ganar el cargo, bajo qué supuestos? No genérico — debe nombrar el candidato y el rol.

5. El "executive_summary" debe leerse como introducción de un partner a un cliente: 4-6 oraciones que posicionen al candidato (años, last role, industria, principal fortaleza, principal riesgo, recomendación).

6. "differentiation": en 1-2 oraciones, ¿qué hace a este candidato distinto del perfil típico que el mercado entregará para este cargo?

7. "career_trajectory":
   - tenure_stability: "Estable" (>3 años promedio), "Mixta" (1-3), "Frecuente" (<1.5)
   - progression: descripción narrativa del arco (ej. "Ascenso clásico Consultant → Manager → Partner en 12 años, luego salto a emprendimiento")
   - current_phase: "Emprendedor", "Ejecutivo corporativo", "Operativo", "Transición", "Consultor independiente"
   - narrative: 2-3 oraciones contando la historia de la carrera

8. "cultural_fit_signals": señales detectables del perfil. Ejemplos:
   - {"signal": "Pasos por consultoría top tier sugieren disciplina analítica y orientación a cliente", "indicator": "Positive"}
   - {"signal": "Múltiples emprendimientos pueden tensionar con cultura corporativa de retail jerárquico", "indicator": "Risk"}

9. "compensation_signals": una oración. Estimación de rango basado en seniority + último cargo (sin inventar números si no hay base; di "requiere validación en entrevista").

10. "interview_questions_detailed": 6-10 preguntas, cada una con:
    - question: la pregunta exacta a hacer
    - objective: qué validar (ej. "Validar gestión de P&L USD 50M+")
    - priority: "Alta" / "Media" / "Baja"
    Las preguntas deben ser específicas al candidato y al cargo, NO genéricas.

11. "dimension_scores": usa el scoring_model del spec si está. Si no, usa estas 10 dimensiones con sus pesos:
    - Requisitos excluyentes (20), Experiencia relevante (15), Calce industria/mercado (10),
    - Seniority y responsabilidad (10), Competencias técnicas (10), Competencias funcionales (10),
    - Logros e impacto (10), Formación y certificaciones (5), Trayectoria y estabilidad (5), Riesgos (5).
    Total = 100. Para cada dimensión: score (entero), max_score, evidence_level ("Alta"/"Media"/"Baja"), rationale (1-2 oraciones citando el perfil), supporting_evidence (1-3 citas literales del perfil).

12. "total_score" debe ser la suma de todos los dimension_scores. score_category:
    - 85+: "Muy alto calce"
    - 70-84: "Buen calce"
    - 55-69: "Calce parcial"
    - 40-54: "Bajo calce"
    - <40: "No recomendado"

13. recommendation: una acción accionable (ej. "Priorizar entrevista de presentación con cliente", "Avanzar a entrevista exploratoria con consultor", "Mantener en reserva pendiente de validar gestión retail", "No avanzar").

14. final_verdict: 1 oración con el veredicto explícito.

15. Lenguaje: español neutro de negocios. Sin emojis. Sin tono jerárquico ni adulación. Honestidad calibrada.

OUTPUT: SOLO JSON válido siguiendo el schema. Sin markdown, sin explicaciones fuera del JSON."""


USER_TEMPLATE = """Evalúa este candidato contra el perfil objetivo. Construye una evaluación 360 nivel partner.

PERFIL OBJETIVO (lo que busca el cliente):
{spec_json}

CANDIDATO (perfil estructurado):
{profile_json}

Devuelve SOLO el JSON con los campos:
- total_score (int 0-100)
- score_category (string)
- recommendation (string accionable)
- executive_summary (4-6 oraciones)
- talent_thesis (2-3 oraciones nombrando candidato y rol)
- final_verdict (1 oración)
- differentiation (1-2 oraciones)
- dimension_scores (lista de objetos con dimension, score, max_score, evidence_level, rationale, supporting_evidence)
- strengths_detailed (lista de objetos: title, detail, evidence) — 4-7 fortalezas calzadas al cargo
- critical_gaps_detailed (lista de objetos: requirement, reason, impact, evidence, mitigation)
- opportunities (lista de objetos: title, detail, evidence) — habilidades/experiencias transferibles que el cliente puede no estar valorando
- transferable_skills (lista de strings cortos)
- weaknesses (lista de strings)
- risks_detailed (lista de objetos: risk, validation)
- red_flags (lista de strings, vacía si no hay)
- career_trajectory (objeto: tenure_stability, progression, current_phase, narrative)
- cultural_fit_signals (lista de objetos: signal, indicator)
- interview_questions_detailed (lista de objetos: question, objective, priority) — 6-10 preguntas
- reference_check_focus (lista de strings — qué validar en referencias)
- onboarding_considerations (lista de strings)
- compensation_signals (string)
- supporting_evidence (lista de strings — citas literales del perfil)
"""


# --- Public entry -------------------------------------------------------------


def ai_evaluate_candidate(
    profile: CandidateProfile, spec: PositionSpec
) -> dict[str, Any] | None:
    """Llama al modelo y devuelve el payload validado o None si fallback aplica."""
    profile_payload = _profile_block(profile)
    spec_payload = _spec_block(spec)

    user_prompt = USER_TEMPLATE.format(
        spec_json=json.dumps(spec_payload, ensure_ascii=False, default=str),
        profile_json=json.dumps(profile_payload, ensure_ascii=False, default=str),
    )

    raw = generate_structured_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        purpose="candidate_evaluation",
        temperature=0.3,
    )
    if raw is None:
        return None

    try:
        validated = _EvaluationLLMOutput.model_validate(raw)
    except ValidationError as error:
        logger.warning("Evaluation LLM output inválido: %s", error)
        return None

    # Re-sumamos total_score por seguridad (el modelo a veces se equivoca).
    summed = sum(d.score for d in validated.dimension_scores) if validated.dimension_scores else validated.total_score
    summed = max(0, min(100, summed))

    # Derivamos los campos plain-list para mantener compatibilidad con columnas.
    strengths_text = [s.title for s in validated.strengths_detailed if s.title]
    critical_gaps_dict = [
        {
            "requirement": g.requirement,
            "reason": g.reason,
            "impact": g.impact,
            "evidence": g.evidence,
            "mitigation": g.mitigation,
        }
        for g in validated.critical_gaps_detailed
    ]
    risks_text = [r.risk for r in validated.risks_detailed if r.risk]
    interview_text = [q.question for q in validated.interview_questions_detailed if q.question]

    ai_assessment = validated.model_dump()
    ai_assessment["total_score_recomputed"] = summed

    return {
        "total_score": summed,
        "score_category": validated.score_category,
        "recommendation": validated.recommendation,
        "executive_summary": validated.executive_summary,
        "dimension_scores": [d.model_dump() for d in validated.dimension_scores],
        "critical_gaps": critical_gaps_dict,
        "strengths": strengths_text,
        "weaknesses": validated.weaknesses,
        "risks": risks_text,
        "interview_questions": interview_text,
        "supporting_evidence": validated.supporting_evidence,
        "final_verdict": validated.final_verdict,
        "ai_assessment": ai_assessment,
        "model_version": MODEL_TAG,
        "prompt_version": PROMPT_VERSION,
    }
