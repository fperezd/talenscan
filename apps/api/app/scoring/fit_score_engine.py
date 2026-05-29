"""Motor de evaluación 360.

Estrategia (alineada con AGENTS.md §5):
1. Intentar evaluación con IA (gpt-4o-mini, JSON mode, Pydantic).
2. Si IA no está disponible o falla, usar evaluador determinista enriquecido
   que sigue heurísticas de senior headhunter: brechas, transferibilidad,
   trayectoria, oportunidades.
"""

from __future__ import annotations

import logging
import statistics
import unicodedata
from typing import Any

from app.ai.evaluator import ai_evaluate_candidate
from app.models.candidate_profile import CandidateProfile
from app.models.position_spec import PositionSpec

logger = logging.getLogger(__name__)


# --- utilidades ---------------------------------------------------------------


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().split())


def _contains(text: str, target: str) -> bool:
    target_norm = _normalize(target)
    if not target_norm:
        return False
    return target_norm in _normalize(text)


def _any_contains(text: str, targets: list[str]) -> bool:
    return any(_contains(text, t) for t in targets if t)


def _score_category(score: int) -> tuple[str, str]:
    if score >= 85:
        return "Muy alto calce", "Priorizar entrevista de presentación con cliente."
    if score >= 70:
        return "Buen calce", "Avanzar a entrevista exploratoria con consultor."
    if score >= 55:
        return "Calce parcial", "Validar brechas en entrevista corta antes de avanzar."
    if score >= 40:
        return "Bajo calce", "Mantener en reserva, no priorizar."
    return "No recomendado", "No avanzar para este mandato."


# --- evaluador determinista enriquecido --------------------------------------


def _rule_based_evaluation(
    profile: CandidateProfile, spec: PositionSpec
) -> dict[str, Any]:
    """Evaluación heurística cuando IA no aplica.

    Genera el mismo shape rico que la IA (opportunities, transferable_skills,
    trajectory, talent_thesis, etc.), inferido de las señales del perfil.
    """
    corpus_parts = [
        " ".join(profile.industries or []),
        " ".join(profile.education or []),
        " ".join(profile.certifications or []),
        " ".join(profile.tools or []),
        " ".join(profile.achievements or []),
        " ".join(profile.evidence_snippets or []),
        " ".join(
            f"{r.get('title','')} {r.get('company','')} {' '.join(r.get('responsibilities',[]) or [])}"
            for r in (profile.roles or [])
            if isinstance(r, dict)
        ),
        profile.current_position or "",
        profile.current_company or "",
    ]
    corpus = " ".join(corpus_parts)

    # --- Requisitos excluyentes -------------------------------------------------
    must_requirements = spec.must_have_requirements or []
    matched_must = 0
    matched_must_items: list[str] = []
    critical_gaps: list[dict[str, str]] = []
    for requirement in must_requirements:
        req_name = str(requirement.get("requisito", "")).strip()
        if not req_name:
            continue
        if _contains(corpus, req_name):
            matched_must += 1
            matched_must_items.append(req_name)
        else:
            critical_gaps.append(
                {
                    "requirement": req_name,
                    "reason": "No se evidenció en el perfil estructurado.",
                    "impact": "Puede limitar el desempeño inicial en el rol.",
                    "evidence": "No evidenciado en el CV",
                    "mitigation": "Validar en entrevista con casos concretos del candidato.",
                }
            )

    must_total = len(must_requirements) or 1
    must_ratio = matched_must / must_total
    must_score = round(must_ratio * 20)

    # --- Industria --------------------------------------------------------------
    target_industries = spec.target_industries or []
    industry_hit = _any_contains(corpus, target_industries) if target_industries else False
    industry_score = 10 if industry_hit else 4
    matched_industries = [
        ind for ind in (profile.industries or [])
        if any(_contains(t, ind) or _contains(ind, t) for t in target_industries)
    ]

    # --- Experiencia y seniority -----------------------------------------------
    years = profile.total_years_experience or 0
    if years >= 15:
        experience_score = 15
    elif years >= 10:
        experience_score = 13
    elif years >= 6:
        experience_score = 11
    elif years >= 3:
        experience_score = 8
    else:
        experience_score = 5

    seniority_target = (spec.title or "").lower()
    target_is_executive = any(k in seniority_target for k in ("gerente", "director", "vp", "ceo", "cfo", "head", "presidente"))
    candidate_is_executive = profile.inferred_seniority in {"C-Level", "VP", "Director", "Manager"}
    if target_is_executive and candidate_is_executive:
        seniority_score = 10
    elif candidate_is_executive:
        seniority_score = 8
    elif profile.inferred_seniority == "Senior":
        seniority_score = 7
    else:
        seniority_score = 5

    # --- Competencias técnicas / funcionales -----------------------------------
    technical_targets = spec.technical_skills or []
    technical_hits = [t for t in technical_targets if _contains(corpus, t)]
    tech_score = min(10, 3 + len(technical_hits) * 2) if technical_targets else (
        min(10, 4 + len(profile.tools or []) // 4)
    )

    functional_targets = (spec.functional_skills or []) + (spec.leadership_skills or [])
    functional_hits = [t for t in functional_targets if _contains(corpus, t)]
    functional_score = min(10, 3 + len(functional_hits) * 2) if functional_targets else (
        min(10, len(profile.roles or []) * 2)
    )

    # --- Logros / impacto ------------------------------------------------------
    achievements = profile.achievements or []
    impact_score = min(10, 3 + len(achievements) * 2) if achievements else 3

    # --- Formación / certificaciones -------------------------------------------
    edu_score = 0
    if profile.education:
        edu_score += 3
    if profile.certifications:
        edu_score += 2
    edu_score = min(5, edu_score) if (profile.education or profile.certifications) else 2

    # --- Trayectoria / estabilidad ---------------------------------------------
    role_durations = [
        float(r.get("duration_years", 0) or 0)
        for r in (profile.roles or [])
        if isinstance(r, dict)
    ]
    avg_tenure = statistics.fmean(role_durations) if role_durations else 0
    if avg_tenure >= 3:
        tenure_stability = "Estable"
        stability_score = 5
    elif avg_tenure >= 1.5:
        tenure_stability = "Mixta"
        stability_score = 4
    elif role_durations:
        tenure_stability = "Frecuente"
        stability_score = 2
    else:
        tenure_stability = "No evidenciado"
        stability_score = 3

    # --- Riesgos ---------------------------------------------------------------
    risk_score = max(0, 5 - min(5, len(critical_gaps)))

    total_score = max(
        0,
        min(
            100,
            must_score
            + experience_score
            + industry_score
            + seniority_score
            + tech_score
            + functional_score
            + impact_score
            + edu_score
            + stability_score
            + risk_score,
        ),
    )

    score_category, recommendation = _score_category(total_score)

    # --- Dimension scores con justificación ------------------------------------
    dimension_scores = [
        {
            "dimension": "Requisitos excluyentes",
            "score": must_score,
            "max_score": 20,
            "evidence_level": "Alta" if must_ratio >= 0.8 else "Media" if must_ratio >= 0.5 else "Baja",
            "rationale": (
                f"Cumple {matched_must}/{must_total} requisitos excluyentes verificables en el perfil."
                if must_requirements else "No se definieron requisitos excluyentes en el perfil objetivo."
            ),
            "supporting_evidence": matched_must_items[:3] or (profile.evidence_snippets or [])[:2],
        },
        {
            "dimension": "Experiencia relevante",
            "score": experience_score,
            "max_score": 15,
            "evidence_level": "Alta" if years >= 10 else "Media" if years >= 5 else "Baja",
            "rationale": (
                f"{years} años de experiencia totales reportados en el perfil."
                if years else "No se pudo cuantificar años de experiencia totales."
            ),
            "supporting_evidence": [
                f"{r.get('title','')} en {r.get('company','')} ({r.get('start_date','')}-{r.get('end_date','')})"
                for r in (profile.roles or [])[:3]
                if isinstance(r, dict)
            ],
        },
        {
            "dimension": "Calce industria / mercado",
            "score": industry_score,
            "max_score": 10,
            "evidence_level": "Alta" if industry_hit else "Baja",
            "rationale": (
                f"Industrias del candidato ({', '.join(profile.industries or []) or '—'}) "
                + (
                    f"cruzan con objetivo ({', '.join(target_industries)})." if industry_hit
                    else f"no cruzan directamente con objetivo ({', '.join(target_industries) or '—'})."
                )
            ),
            "supporting_evidence": matched_industries or (profile.industries or [])[:3],
        },
        {
            "dimension": "Seniority y responsabilidad",
            "score": seniority_score,
            "max_score": 10,
            "evidence_level": "Alta" if candidate_is_executive else "Media",
            "rationale": (
                f"Seniority inferido: {profile.inferred_seniority or 'No determinado'}. "
                f"Cargo actual: {profile.current_position or '—'}."
            ),
            "supporting_evidence": [profile.current_position] if profile.current_position else [],
        },
        {
            "dimension": "Competencias técnicas",
            "score": tech_score,
            "max_score": 10,
            "evidence_level": "Alta" if len(technical_hits) >= 3 else "Media" if technical_hits else "Baja",
            "rationale": (
                f"Coincide con {len(technical_hits)}/{len(technical_targets)} técnicas del perfil objetivo."
                if technical_targets else "Sin requisitos técnicos explícitos."
            ),
            "supporting_evidence": technical_hits[:5],
        },
        {
            "dimension": "Competencias funcionales",
            "score": functional_score,
            "max_score": 10,
            "evidence_level": "Alta" if len(functional_hits) >= 3 else "Media",
            "rationale": (
                f"Coincide con {len(functional_hits)}/{len(functional_targets)} competencias funcionales."
                if functional_targets else "Sin requisitos funcionales explícitos."
            ),
            "supporting_evidence": functional_hits[:5],
        },
        {
            "dimension": "Logros e impacto",
            "score": impact_score,
            "max_score": 10,
            "evidence_level": "Alta" if len(achievements) >= 4 else "Media" if achievements else "Baja",
            "rationale": f"{len(achievements)} logros evidenciados en el perfil.",
            "supporting_evidence": achievements[:3],
        },
        {
            "dimension": "Formación y certificaciones",
            "score": edu_score,
            "max_score": 5,
            "evidence_level": "Alta" if edu_score >= 4 else "Media",
            "rationale": (
                f"{len(profile.education or [])} formaciones y "
                f"{len(profile.certifications or [])} certificaciones evidenciadas."
            ),
            "supporting_evidence": (profile.education or [])[:2] + (profile.certifications or [])[:2],
        },
        {
            "dimension": "Trayectoria y estabilidad",
            "score": stability_score,
            "max_score": 5,
            "evidence_level": "Media",
            "rationale": (
                f"Permanencia promedio {avg_tenure:.1f} años por rol — tendencia {tenure_stability.lower()}."
            ),
            "supporting_evidence": [
                f"{r.get('title','')}: {r.get('duration_years', 0)} años"
                for r in (profile.roles or [])[:3]
                if isinstance(r, dict)
            ],
        },
        {
            "dimension": "Riesgos y brechas",
            "score": risk_score,
            "max_score": 5,
            "evidence_level": "Alta" if not critical_gaps else "Media",
            "rationale": (
                f"{len(critical_gaps)} brecha(s) crítica(s) detectada(s)."
                if critical_gaps else "Sin brechas críticas detectadas."
            ),
            "supporting_evidence": [g["requirement"] for g in critical_gaps[:3]],
        },
    ]

    # --- Strengths -------------------------------------------------------------
    strengths_detailed: list[dict[str, str]] = []
    if matched_must_items:
        strengths_detailed.append({
            "title": f"Cumple {len(matched_must_items)} requisitos excluyentes clave",
            "detail": "Las exigencias bloqueantes del perfil objetivo están evidenciadas en la trayectoria.",
            "evidence": "; ".join(matched_must_items[:3]),
        })
    if years >= 10 and candidate_is_executive:
        strengths_detailed.append({
            "title": f"Trayectoria ejecutiva consolidada ({years} años)",
            "detail": f"Seniority {profile.inferred_seniority} con experiencia acumulada que cubre con holgura el rango esperado.",
            "evidence": (profile.current_position or "") + (f" en {profile.current_company}" if profile.current_company else ""),
        })
    if industry_hit:
        strengths_detailed.append({
            "title": "Experiencia directa en la industria objetivo",
            "detail": "Conoce dinámicas, players y benchmarks del sector requerido.",
            "evidence": ", ".join(matched_industries[:3]),
        })
    if achievements:
        strengths_detailed.append({
            "title": "Logros medibles documentados",
            "detail": "Presenta evidencia de impacto cuantificado en roles anteriores.",
            "evidence": achievements[0][:200],
        })
    if profile.languages and len(profile.languages) >= 2:
        strengths_detailed.append({
            "title": "Perfil multilingüe",
            "detail": "Capacidad de operar en contextos regionales o globales.",
            "evidence": ", ".join(profile.languages[:4]),
        })

    # --- Oportunidades / habilidades transferibles -----------------------------
    opportunities: list[dict[str, str]] = []
    transferable_skills: list[str] = []
    # Si tiene mucho liderazgo total pero poco en la industria objetivo
    if not industry_hit and candidate_is_executive and years >= 10:
        opportunities.append({
            "title": "Liderazgo transferible cross-industry",
            "detail": (
                f"{years} años de gestión ejecutiva en otras industrias se traducen en capacidades "
                f"de liderazgo, P&L y transformación que el cliente puede subestimar al filtrar por "
                f"industria objetivo. Vale la pena exponer este ángulo al cliente."
            ),
            "evidence": "; ".join(
                f"{r.get('title','')} en {r.get('company','')}"
                for r in (profile.roles or [])[:3]
                if isinstance(r, dict)
            ),
        })
        transferable_skills.append("Liderazgo ejecutivo cross-industry")

    if "founder" in (profile.current_position or "").lower() or "ceo" in (profile.current_position or "").lower():
        opportunities.append({
            "title": "Mentalidad emprendedora y agilidad operativa",
            "detail": (
                "El haber liderado emprendimientos propios indica autonomía, gestión de incertidumbre "
                "y velocidad de decisión — atributos escasos en pools tradicionales de búsqueda ejecutiva."
            ),
            "evidence": f"{profile.current_position} en {profile.current_company}",
        })
        transferable_skills.append("Mentalidad emprendedora / fundador")

    if any("consult" in i.lower() for i in (profile.industries or [])):
        opportunities.append({
            "title": "Background de consultoría top tier",
            "detail": (
                "Paso por consultoría sugiere disciplina analítica, estructuración de problemas y "
                "exposición a múltiples industrias y modelos de negocio."
            ),
            "evidence": ", ".join([i for i in (profile.industries or []) if "consult" in i.lower()]),
        })
        transferable_skills.append("Pensamiento estructurado de consultoría")

    if profile.certifications:
        transferable_skills.append("Certificaciones validables: " + ", ".join(profile.certifications[:3]))

    # --- Weaknesses ------------------------------------------------------------
    weaknesses: list[str] = []
    if critical_gaps:
        weaknesses.append(
            f"Existen {len(critical_gaps)} brechas en requisitos excluyentes que requieren validación."
        )
    if not industry_hit and target_industries:
        weaknesses.append(
            f"Experiencia directa en industria objetivo ({', '.join(target_industries[:2])}) no evidenciada."
        )
    if not profile.languages:
        weaknesses.append("No se evidencian idiomas en el perfil estructurado.")
    if not profile.certifications:
        weaknesses.append("No se evidencian certificaciones formales relevantes.")
    if avg_tenure and avg_tenure < 1.5:
        weaknesses.append(
            f"Permanencia promedio baja ({avg_tenure:.1f} años) — validar motivos en entrevista."
        )

    # --- Risks -----------------------------------------------------------------
    risks_detailed = [
        {
            "risk": f"Validar en entrevista: {gap['requirement']}",
            "validation": gap.get("mitigation") or "Caso concreto + referencia.",
        }
        for gap in critical_gaps[:5]
    ]
    if not industry_hit and target_industries:
        risks_detailed.append({
            "risk": f"Curva de aprendizaje en industria {target_industries[0]}.",
            "validation": "Validar mediante caso de negocio en entrevista 2.",
        })

    # --- Trajectory ------------------------------------------------------------
    roles_list = profile.roles or []
    progression = ""
    if len(roles_list) >= 2:
        first_title = roles_list[-1].get("title", "") if isinstance(roles_list[-1], dict) else ""
        last_title = roles_list[0].get("title", "") if isinstance(roles_list[0], dict) else ""
        if first_title and last_title:
            progression = f"De {first_title} a {last_title}"

    current_phase = "No determinado"
    cp = (profile.current_position or "").lower()
    if "founder" in cp or "ceo" in cp:
        current_phase = "Emprendedor / CEO"
    elif candidate_is_executive:
        current_phase = "Ejecutivo corporativo"
    elif "consultor" in cp or "advisor" in cp or "mentor" in cp:
        current_phase = "Consultor independiente / Advisor"

    career_trajectory = {
        "tenure_stability": tenure_stability,
        "progression": progression or "Trayectoria con múltiples roles.",
        "current_phase": current_phase,
        "narrative": (
            f"{years} años de experiencia con {len(roles_list)} roles documentados. "
            f"Permanencia promedio {avg_tenure:.1f} años por rol. "
            f"Fase actual: {current_phase}."
        ),
    }

    # --- Cultural fit signals --------------------------------------------------
    cultural_fit_signals: list[dict[str, str]] = []
    if any("consult" in i.lower() for i in (profile.industries or [])):
        cultural_fit_signals.append({
            "signal": "Background de consultoría sugiere disciplina analítica y orientación a cliente.",
            "indicator": "Positive",
        })
    if current_phase.startswith("Emprendedor"):
        cultural_fit_signals.append({
            "signal": "Múltiples emprendimientos pueden tensionar con culturas corporativas jerárquicas.",
            "indicator": "Risk",
        })
    if avg_tenure >= 4:
        cultural_fit_signals.append({
            "signal": "Permanencias largas sugieren tolerancia a estructuras estables y construcción de equipo.",
            "indicator": "Positive",
        })

    # --- Talent thesis ---------------------------------------------------------
    candidate_name = ""
    if profile.parsed_json and isinstance(profile.parsed_json, dict):
        candidate_name = str(profile.parsed_json.get("candidate_name") or "")
    candidate_name = candidate_name or "El candidato"

    talent_thesis = (
        f"{candidate_name} ofrece {years} años de experiencia y seniority "
        f"{profile.inferred_seniority or 'a confirmar'}, con calce {score_category.lower()} "
        f"contra el cargo {spec.title}. "
        + (
            f"Su ángulo más fuerte es {strengths_detailed[0]['title'].lower()}. "
            if strengths_detailed else ""
        )
        + (
            f"El riesgo principal a validar es {critical_gaps[0]['requirement']}."
            if critical_gaps else "No se identificaron brechas críticas bloqueantes."
        )
    )

    # --- Differentiation -------------------------------------------------------
    differentiation = (
        f"Combinación de seniority {profile.inferred_seniority or 'ejecutivo'}, "
        f"{years} años de carrera y "
        + (
            "experiencia directa en industria objetivo." if industry_hit
            else "experiencia transferible cross-industry."
        )
    )

    # --- Interview questions ---------------------------------------------------
    interview_questions_detailed: list[dict[str, str]] = []
    for gap in critical_gaps[:3]:
        interview_questions_detailed.append({
            "question": f"¿Qué evidencia concreta tienes sobre: {gap['requirement']}?",
            "objective": f"Validar requisito excluyente: {gap['requirement']}",
            "priority": "Alta",
        })
    if not industry_hit and target_industries:
        interview_questions_detailed.append({
            "question": (
                f"¿Cómo aplicarías tu experiencia previa al contexto de {target_industries[0]}? "
                "¿Qué supuestos crees que necesitarías validar en los primeros 90 días?"
            ),
            "objective": f"Validar capacidad de transferir aprendizajes a {target_industries[0]}",
            "priority": "Alta",
        })
    if years >= 10:
        interview_questions_detailed.append({
            "question": (
                "Cuéntame de un mandato o iniciativa con P&L que hayas liderado: tamaño, "
                "resultados, equipo y principal aprendizaje."
            ),
            "objective": "Validar gestión de P&L y liderazgo ejecutivo",
            "priority": "Alta",
        })
    interview_questions_detailed.append({
        "question": "¿Qué buscas en tu próximo desafío y qué te haría dejarlo en 6 meses?",
        "objective": "Validar motivación, expectativa de carrera y red flags de fit",
        "priority": "Media",
    })
    for sq in (spec.interview_questions or [])[:3]:
        interview_questions_detailed.append({
            "question": sq,
            "objective": "Pregunta sugerida en el perfil objetivo del cargo",
            "priority": "Media",
        })

    # --- Reference check + onboarding -----------------------------------------
    reference_check_focus: list[str] = []
    if matched_must_items:
        reference_check_focus.append(f"Confirmar evidencia de: {matched_must_items[0]}")
    if years >= 10:
        reference_check_focus.append("Validar resultados cuantificados de gestión de equipo y P&L con ex-jefe.")
    if critical_gaps:
        reference_check_focus.append(
            f"Pedir referencia que valide {critical_gaps[0]['requirement']}."
        )
    reference_check_focus.append("Validar estilo de liderazgo y manejo de stakeholders con un ex-reporte directo.")

    onboarding_considerations: list[str] = []
    if not industry_hit and target_industries:
        onboarding_considerations.append(
            f"Apoyar primeros 90 días con inmersión profunda en {target_industries[0]}."
        )
    if current_phase.startswith("Emprendedor"):
        onboarding_considerations.append(
            "Acompañar transición de modelo emprendedor a estructura corporativa más formal."
        )
    if not onboarding_considerations:
        onboarding_considerations.append("Plan de ramp-up estándar para nivel ejecutivo (90/180/365 días).")

    final_verdict = (
        "Priorizar entrevista — perfil con calce alto y riesgos manejables."
        if total_score >= 70 and not critical_gaps
        else "Avanzar con cautela — validar brechas en entrevista antes de presentar al cliente."
        if total_score >= 55
        else "Mantener en reserva — no priorizar para este mandato."
    )
    if total_score < 40:
        final_verdict = "No avanzar para este mandato — calce insuficiente."

    executive_summary = (
        f"{candidate_name}, con {years} años de experiencia y seniority "
        f"{profile.inferred_seniority or 'por confirmar'} en "
        f"{', '.join(profile.industries[:2]) if profile.industries else 'múltiples industrias'}, "
        f"presenta un calce {score_category.lower()} (score {total_score}/100) contra el cargo "
        f"{spec.title}. "
        + (
            f"Sus fortalezas principales son {', '.join(s['title'].lower() for s in strengths_detailed[:2])}. "
            if strengths_detailed else ""
        )
        + (
            f"Las brechas a validar en entrevista incluyen {', '.join(g['requirement'] for g in critical_gaps[:2])}. "
            if critical_gaps else "No se detectaron brechas críticas. "
        )
        + recommendation
    )

    ai_assessment = {
        "total_score": total_score,
        "score_category": score_category,
        "recommendation": recommendation,
        "executive_summary": executive_summary,
        "talent_thesis": talent_thesis,
        "final_verdict": final_verdict,
        "differentiation": differentiation,
        "dimension_scores": dimension_scores,
        "strengths_detailed": strengths_detailed,
        "critical_gaps_detailed": critical_gaps,
        "opportunities": opportunities,
        "transferable_skills": transferable_skills,
        "weaknesses": weaknesses,
        "risks_detailed": risks_detailed,
        "red_flags": [],
        "career_trajectory": career_trajectory,
        "cultural_fit_signals": cultural_fit_signals,
        "interview_questions_detailed": interview_questions_detailed,
        "reference_check_focus": reference_check_focus,
        "onboarding_considerations": onboarding_considerations,
        "compensation_signals": (
            "Rango estimado requiere validación en entrevista con candidato y benchmark cliente."
        ),
        "supporting_evidence": (profile.evidence_snippets or [])[:8],
    }

    return {
        "total_score": total_score,
        "score_category": score_category,
        "recommendation": recommendation,
        "executive_summary": executive_summary,
        "dimension_scores": dimension_scores,
        "critical_gaps": critical_gaps,
        "strengths": [s["title"] for s in strengths_detailed],
        "weaknesses": weaknesses,
        "risks": [r["risk"] for r in risks_detailed],
        "interview_questions": [q["question"] for q in interview_questions_detailed],
        "supporting_evidence": (profile.evidence_snippets or [])[:8],
        "final_verdict": final_verdict,
        "ai_assessment": ai_assessment,
        "model_version": "talenscan-rules-v2-headhunter",
        "prompt_version": "evaluation-rules-v2",
    }


# --- Public entry -------------------------------------------------------------


def evaluate_candidate(profile: CandidateProfile, spec: PositionSpec) -> dict[str, Any]:
    """Genera evaluación 360. Intenta IA y cae a reglas enriquecidas si no aplica."""
    ai_result = ai_evaluate_candidate(profile, spec)
    if ai_result is not None:
        # Garantizar todos los campos esperados por el caller, incluso si IA omitió alguno.
        ai_result.setdefault("ai_assessment", {})
        return ai_result

    logger.info("Evaluación: usando motor determinista (IA no disponible o falló).")
    return _rule_based_evaluation(profile, spec)
