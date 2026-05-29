"""Servicio: orquesta la generación del PDF comparativo de candidatos.

Recibe un mandate_id y una lista de evaluation_ids; carga la información,
construye el contexto enriquecido (ranking, dimensiones, AI assessment) y
delega el render al generador HTML+WeasyPrint.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.candidate_evaluation import CandidateEvaluation
from app.models.position_spec import PositionSpec
from app.models.search_mandate import SearchMandate
from app.reporting.comparison_report_generator import build_comparison_pdf


def _score_tone(score: int) -> dict[str, str]:
    if score >= 85:
        return {
            "ring": "#6EE7B7", "bg": "#ECFDF5", "text": "#047857",
            "badge_bg": "#D1FAE5", "badge_fg": "#047857",
        }
    if score >= 70:
        return {
            "ring": "#93C5FD", "bg": "#EFF6FF", "text": "#1D4ED8",
            "badge_bg": "#DBEAFE", "badge_fg": "#1D4ED8",
        }
    if score >= 55:
        return {
            "ring": "#FCD34D", "bg": "#FFFBEB", "text": "#B45309",
            "badge_bg": "#FEF3C7", "badge_fg": "#B45309",
        }
    if score >= 40:
        return {
            "ring": "#CBD5E1", "bg": "#F1F5F9", "text": "#475569",
            "badge_bg": "#E2E8F0", "badge_fg": "#475569",
        }
    return {
        "ring": "#FDA4AF", "bg": "#FFF1F2", "text": "#BE123C",
        "badge_bg": "#FFE4E6", "badge_fg": "#BE123C",
    }


def _tenure_tone(value: str) -> str:
    lower = (value or "").lower()
    if "estable" in lower:
        return "positive"
    if "frecuente" in lower:
        return "risk"
    return "neutral"


def _short_name(full: str) -> str:
    parts = (full or "").split()
    if not parts:
        return "—"
    if len(parts) == 1:
        return parts[0][:14]
    return f"{parts[0]} {parts[1][:1]}."


class ComparisonReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _load(
        self, mandate_id: int, evaluation_ids: list[int]
    ) -> tuple[SearchMandate, list[tuple[CandidateEvaluation, Candidate, PositionSpec | None]]]:
        mandate = self.db.get(SearchMandate, mandate_id)
        if mandate is None:
            raise ValueError("Mandato no encontrado")

        bundles: list[tuple[CandidateEvaluation, Candidate, PositionSpec | None]] = []
        for eval_id in evaluation_ids:
            evaluation = self.db.get(CandidateEvaluation, eval_id)
            if evaluation is None:
                continue
            candidate = self.db.get(Candidate, evaluation.candidate_id)
            if candidate is None:
                continue
            position_spec = self.db.get(PositionSpec, evaluation.position_spec_id)
            bundles.append((evaluation, candidate, position_spec))

        if not bundles:
            raise ValueError("No se pudo cargar ninguna evaluación para comparar.")
        return mandate, bundles

    def _build_candidate_block(
        self,
        evaluation: CandidateEvaluation,
        candidate: Candidate,
        is_top: bool,
    ) -> dict[str, Any]:
        ai = {}
        if isinstance(evaluation.evaluation_json, dict):
            ai = evaluation.evaluation_json.get("ai_assessment", {}) or {}

        tone = _score_tone(evaluation.total_score)

        strengths_detailed = ai.get("strengths_detailed") or []
        top_strengths = [s.get("title", "") for s in strengths_detailed[:3] if isinstance(s, dict) and s.get("title")]

        gaps_detailed = ai.get("critical_gaps_detailed") or []
        top_gaps = [g.get("requirement", "") for g in gaps_detailed[:3] if isinstance(g, dict) and g.get("requirement")]

        opportunities = ai.get("opportunities") or []
        top_opportunities = [o.get("title", "") for o in opportunities[:3] if isinstance(o, dict) and o.get("title")]

        career = ai.get("career_trajectory") or {}
        tenure_stability = career.get("tenure_stability") or "—"
        current_phase = career.get("current_phase") or "—"

        questions_detailed = ai.get("interview_questions_detailed") or []
        priority_questions = [
            q.get("question", "")
            for q in questions_detailed
            if isinstance(q, dict) and str(q.get("priority", "")).lower().startswith("alta")
        ][:3]
        if not priority_questions:
            priority_questions = [q.get("question", "") for q in questions_detailed[:3] if isinstance(q, dict)]

        return {
            "name": candidate.full_name,
            "short_name": _short_name(candidate.full_name),
            "current_position": candidate.current_position or "—",
            "current_company": candidate.current_company or "—",
            "score": evaluation.total_score,
            "score_category": evaluation.score_category,
            "tone": tone,
            "is_top": is_top,
            "talent_thesis": ai.get("talent_thesis") or "",
            "gaps_count": len(gaps_detailed) or len(evaluation.critical_gaps or []),
            "strengths_count": len(strengths_detailed) or len(evaluation.strengths or []),
            "opportunities_count": len(opportunities),
            "current_phase": current_phase,
            "tenure_stability": tenure_stability,
            "tenure_stability_tone": _tenure_tone(tenure_stability),
            "recommendation": evaluation.recommendation,
            "top_strengths": top_strengths,
            "top_gaps": top_gaps,
            "top_opportunities": top_opportunities,
            "priority_questions": priority_questions,
            "reference_check_focus": (ai.get("reference_check_focus") or [])[:3],
            "onboarding_considerations": (ai.get("onboarding_considerations") or [])[:3],
            "dimension_scores": evaluation.dimension_scores or [],
            "evaluation_id": evaluation.id,
            "candidate_id": candidate.id,
        }

    def _build_dimension_rows(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Unión de dimensiones; marca el mejor por fila."""
        order: list[str] = []
        max_by_name: dict[str, int] = {}
        for c in candidates:
            for dim in c.get("dimension_scores") or []:
                if not isinstance(dim, dict):
                    continue
                name = str(dim.get("dimension", ""))
                if not name:
                    continue
                if name not in order:
                    order.append(name)
                max_val = int(dim.get("max_score") or 0)
                if max_val > max_by_name.get(name, 0):
                    max_by_name[name] = max_val

        rows: list[dict[str, Any]] = []
        for name in order:
            max_score = max_by_name.get(name, 10) or 10
            cells: list[dict[str, Any]] = []
            best_score = -1
            best_index = -1
            for idx, c in enumerate(candidates):
                found = next(
                    (d for d in (c.get("dimension_scores") or []) if isinstance(d, dict) and d.get("dimension") == name),
                    None,
                )
                if found is None:
                    cells.append({"score": None, "ratio": 0, "is_best": False})
                    continue
                score = int(found.get("score") or 0)
                if score > best_score:
                    best_score = score
                    best_index = idx
                ratio = score / max_score if max_score else 0
                cells.append({"score": score, "ratio": ratio, "is_best": False})
            if best_index >= 0 and len(candidates) > 1:
                cells[best_index]["is_best"] = True
            rows.append({"name": name, "max": max_score, "cells": cells})
        return rows

    def _build_shortlist_message(
        self, candidates: list[dict[str, Any]], target_role: str
    ) -> tuple[str, str, str]:
        if not candidates:
            return ("Sin candidatos", "", "")

        ranked = sorted(candidates, key=lambda c: c["score"], reverse=True)
        top = ranked[0]
        n = len(candidates)

        clean = [c for c in ranked if c["gaps_count"] == 0]
        risky = [c for c in ranked if c["gaps_count"] > 0]

        if n == 1:
            headline = f"{top['name']} es la única opción evaluada para {target_role}."
            rationale = (
                f"Score {top['score']}/100 ({top['score_category']}). "
                f"{top.get('talent_thesis') or top['recommendation']}"
            )
            return headline, rationale, ""

        if len(clean) >= 1:
            names = ", ".join(c["name"] for c in clean[:3])
            headline = f"Priorizar a {names} — sin brechas críticas y mejor calce."
            rationale = (
                f"De {n} candidatos comparados, {len(clean)} no presenta(n) brechas críticas. "
                f"El de mayor score es {top['name']} ({top['score']}/100, {top['score_category']}). "
                f"{top.get('talent_thesis') or top['recommendation']}"
            )
            note = ""
            if len(clean) < n:
                note = (
                    f"Los restantes {len(risky)} candidato(s) tienen brechas críticas a validar; "
                    "vale la pena considerarlos solo si las brechas son mitigables vía referencias o entrevista profunda."
                )
            return headline, rationale, note

        # Todos con brechas
        headline = f"Sin candidatos limpios: priorizar a {top['name']} con validación de brechas."
        rationale = (
            f"Los {n} candidatos comparados presentan brechas críticas. {top['name']} lidera el score "
            f"({top['score']}/100, {top['score_category']}). "
            f"{top.get('talent_thesis') or top['recommendation']}"
        )
        note = (
            "Recomendación: profundizar mapeo de mercado o flexibilizar requisitos excluyentes "
            "antes de presentar al cliente."
        )
        return headline, rationale, note

    def generate_pdf(self, mandate_id: int, evaluation_ids: list[int]) -> bytes:
        mandate, bundles = self._load(mandate_id, evaluation_ids)

        # Pre-compute top score
        top_id = max(bundles, key=lambda b: b[0].total_score)[0].id

        candidates: list[dict[str, Any]] = []
        for evaluation, candidate, _spec in bundles:
            block = self._build_candidate_block(evaluation, candidate, evaluation.id == top_id)
            candidates.append(block)

        # Stats
        scores = [c["score"] for c in candidates]
        avg_score = round(sum(scores) / len(scores)) if scores else 0
        candidates_count = len(candidates)
        without_gaps = sum(1 for c in candidates if c["gaps_count"] == 0)
        # Industria: si tenure_stability o recommendation menciona "industria objetivo" — proxy: cuento candidatos cuya recomendación no marca brecha de industria
        target_industries = (mandate.target_industries or []) + ([mandate.industry] if mandate.industry else [])

        def matches_industry(c: dict[str, Any]) -> bool:
            # Heurística: si NO tiene brecha que contenga "industria" o "retail" del rubro, asumimos OK.
            gaps_text = " ".join(c.get("top_gaps") or []).lower()
            target_text = " ".join(target_industries).lower()
            if not target_text:
                return True
            return target_text not in gaps_text and "industria" not in gaps_text

        candidates_with_industry = sum(1 for c in candidates if matches_industry(c))

        top_scorer_info = next(c for c in candidates if c["is_top"])

        headline, rationale, note = self._build_shortlist_message(
            candidates, mandate.target_role or "este cargo"
        )

        context = {
            "mandate_title": mandate.search_title or "Mandato sin título",
            "client_name": mandate.client_name or "—",
            "target_role": mandate.target_role or "—",
            "industry": mandate.industry or "—",
            "city": mandate.city or "—",
            "country": mandate.country or "—",
            "candidates_count": candidates_count,
            "candidates": candidates,
            "avg_score": avg_score,
            "candidates_without_gaps_count": without_gaps,
            "candidates_with_industry_count": candidates_with_industry,
            "top_scorer": {
                "name": top_scorer_info["name"],
                "score": top_scorer_info["score"],
                "category": top_scorer_info["score_category"],
            },
            "shortlist_headline": headline,
            "shortlist_rationale": rationale,
            "shortlist_note": note,
            "dimension_rows": self._build_dimension_rows(candidates),
        }

        return build_comparison_pdf(context)
