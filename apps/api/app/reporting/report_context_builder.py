from typing import Any

from app.models.candidate import Candidate
from app.models.candidate_evaluation import CandidateEvaluation
from app.models.position_spec import PositionSpec
from app.models.search_mandate import SearchMandate


def build_report_context(
    evaluation: CandidateEvaluation,
    candidate: Candidate | None,
    position_spec: PositionSpec | None,
    mandate: SearchMandate | None,
) -> dict[str, object]:
    """Construye el contexto para los generadores de PDF/Word.

    Extrae el sub-bloque `ai_assessment` (si está) y lo expone bajo claves de
    primer nivel para que los generadores no tengan que conocer la estructura
    interna del JSON.
    """
    raw_json = evaluation.evaluation_json or {}
    ai: dict[str, Any] = (
        raw_json.get("ai_assessment", {}) if isinstance(raw_json, dict) else {}
    ) or {}

    return {
        "evaluation_id": evaluation.id,
        "candidate_name": candidate.full_name if candidate else f"Candidato #{evaluation.candidate_id}",
        "candidate_position": candidate.current_position if candidate else None,
        "candidate_company": candidate.current_company if candidate else None,
        "candidate_email": candidate.email if candidate else None,
        "candidate_phone": candidate.phone if candidate else None,
        "mandate_title": mandate.search_title if mandate else "Mandato no disponible",
        "client_name": mandate.client_name if mandate else "Cliente no disponible",
        "target_role": mandate.target_role if mandate else "Cargo no disponible",
        "score": evaluation.total_score,
        "score_category": evaluation.score_category,
        "recommendation": evaluation.recommendation,
        "summary": evaluation.executive_summary,
        "strengths": evaluation.strengths,
        "weaknesses": evaluation.weaknesses,
        "critical_gaps": evaluation.critical_gaps,
        "risks": evaluation.risks,
        "questions": evaluation.interview_questions,
        "evidence": evaluation.supporting_evidence,
        "dimensions": evaluation.dimension_scores,
        "final_verdict": evaluation.final_verdict,
        "model_version": evaluation.model_version,
        "prompt_version": evaluation.prompt_version,
        "position_spec_title": position_spec.title if position_spec else "Perfil objetivo no disponible",
        # --- Bloque IA (headhunter-grade) ---------------------------------
        "talent_thesis": ai.get("talent_thesis", ""),
        "differentiation": ai.get("differentiation", ""),
        "strengths_detailed": ai.get("strengths_detailed", []),
        "critical_gaps_detailed": ai.get("critical_gaps_detailed", []),
        "opportunities": ai.get("opportunities", []),
        "transferable_skills": ai.get("transferable_skills", []),
        "risks_detailed": ai.get("risks_detailed", []),
        "red_flags": ai.get("red_flags", []),
        "career_trajectory": ai.get("career_trajectory", {}) or {},
        "cultural_fit_signals": ai.get("cultural_fit_signals", []),
        "interview_questions_detailed": ai.get("interview_questions_detailed", []),
        "reference_check_focus": ai.get("reference_check_focus", []),
        "onboarding_considerations": ai.get("onboarding_considerations", []),
        "compensation_signals": ai.get("compensation_signals", ""),
        "traceability_note": (
            "Informe generado por TalentScan a partir del perfil objetivo del cargo, el perfil del "
            "candidato y el modelo de evaluación 360. La evaluación debe ser revisada por el consultor "
            "responsable antes de ser compartida con el cliente."
        ),
    }
