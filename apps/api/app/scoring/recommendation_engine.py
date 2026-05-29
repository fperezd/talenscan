"""Motor determinístico de recomendaciones de recalibración.

Reglas de negocio (todas con `generated_by="rules"`):
1. Cobertura baja + pocas empresas target → "Agregar empresas target"
2. Brecha de "industria específica" alta → "Ampliar a industrias adyacentes"
3. Mayoría de candidatos con score bajo → "Revisar calibración del perfil"
4. Brecha excluyente >= 50% → "Mover requisito X a deseable o relajarlo"
5. Cobertura > 70% pero shortlist vacía → "Empujar candidatos a shortlist"
6. Sin candidatos evaluados pero perfil generado → "Cargar y evaluar candidatos"
7. Muchos descartes con misma razón → "Recalibrar criterio de descarte"

La IA es opcional y entra después para redactar mejor el copy si el consultor
así lo pide. Por defecto las reglas generan título + reason en lenguaje claro.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from app.models.candidate_evaluation import CandidateEvaluation
from app.models.candidate_pipeline_item import CandidatePipelineItem
from app.models.talent_market_map import TargetCompany


def generate_rule_recommendations(
    *,
    coverage_pct: int,
    target_companies: list[TargetCompany],
    pipeline_items: list[CandidatePipelineItem],
    evaluations_map: dict[int, CandidateEvaluation],
    gaps_data: list[dict[str, Any]],
    shortlisted_count: int,
) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []

    evaluated = [
        it for it in pipeline_items if it.evaluation_id in evaluations_map
    ]
    avg_score = (
        sum(evaluations_map[it.evaluation_id].total_score for it in evaluated)
        / len(evaluated)
        if evaluated
        else 0
    )
    discarded = [it for it in pipeline_items if it.stage == "discarded"]

    # R1: Cobertura baja + pocas empresas target
    if coverage_pct < 30 and len(target_companies) < 5:
        recs.append(
            {
                "title": "Agregar más empresas target",
                "reason": (
                    f"La cobertura actual es de {coverage_pct}% y sólo hay "
                    f"{len(target_companies)} empresas target definidas. "
                    "Ampliar la lista permite mapear más perfiles relevantes."
                ),
                "expected_impact": "Aumentar el universo de candidatos potenciales en 30-50%.",
                "confidence": "high",
                "generated_by": "rules",
            }
        )

    # R2: Brecha de industria alta → industrias adyacentes
    industry_gap = next(
        (g for g in gaps_data if "industria" in g["title"].lower() and g["frequency"] >= 2),
        None,
    )
    if industry_gap:
        pct = int((industry_gap["frequency"] / max(1, industry_gap["total_evaluated"])) * 100)
        recs.append(
            {
                "title": "Ampliar búsqueda a industrias adyacentes",
                "reason": (
                    f"El {pct}% de los candidatos evaluados no cumple el requisito "
                    f"\"{industry_gap['title']}\". El mercado de la industria específica "
                    "parece estrecho; abrir a industrias con procesos similares puede "
                    "ampliar el universo significativamente."
                ),
                "expected_impact": "Doblar o triplicar el universo de candidatos transferibles.",
                "confidence": "high",
                "generated_by": "rules",
            }
        )

    # R3: Score promedio bajo
    if evaluated and avg_score < 55:
        recs.append(
            {
                "title": "Revisar calibración del perfil objetivo",
                "reason": (
                    f"El score promedio de los {len(evaluated)} candidatos evaluados "
                    f"es {int(avg_score)}/100 (calce bajo). Esto sugiere que el "
                    "perfil objetivo es demasiado exigente, o que el mercado "
                    "elegido no calza con los requisitos. Revisar requisitos "
                    "excluyentes con el cliente."
                ),
                "expected_impact": "Mejorar score promedio en 15-25 puntos al ajustar requisitos.",
                "confidence": "high",
                "generated_by": "rules",
            }
        )

    # R4: Brecha repetida de "excluyente" → relajar
    high_freq_gaps = [g for g in gaps_data if g["impact"] == "high" and g["frequency"] >= 2]
    if evaluated:
        for g in high_freq_gaps[:2]:  # top 2 brechas críticas
            pct = int((g["frequency"] / max(1, g["total_evaluated"])) * 100)
            if pct >= 50:
                recs.append(
                    {
                        "title": f"Considerar relajar requisito: \"{g['title']}\"",
                        "reason": (
                            f"El {pct}% de los candidatos evaluados no cumple este "
                            "requisito catalogado como crítico. Si más de la mitad del "
                            "mercado lo falla, vale evaluar si es realmente excluyente "
                            "o puede moverse a deseable."
                        ),
                        "expected_impact": g.get("recommendation")
                        or "Aumentar significativamente el pool de candidatos viables.",
                        "confidence": "high",
                        "generated_by": "rules",
                    }
                )

    # R5: Cobertura alta pero shortlist vacía
    if coverage_pct >= 70 and len(evaluated) >= 5 and shortlisted_count == 0:
        recs.append(
            {
                "title": "Avanzar candidatos a shortlist",
                "reason": (
                    f"La cobertura es de {coverage_pct}% con {len(evaluated)} "
                    "candidatos evaluados, pero ninguno está en shortlist. Revisar "
                    "los de mayor calce y armar la primera shortlist para el cliente."
                ),
                "expected_impact": "Acelerar el ciclo de decisión y obtener feedback del cliente.",
                "confidence": "medium",
                "generated_by": "rules",
            }
        )

    # R6: Pipeline sin evaluaciones
    if pipeline_items and not evaluated:
        recs.append(
            {
                "title": "Ejecutar Evaluaciones 360 sobre el pipeline",
                "reason": (
                    f"Hay {len(pipeline_items)} candidatos en el pipeline pero "
                    "ninguno tiene Evaluación 360 generada. Sin evaluaciones no se "
                    "pueden detectar brechas ni calibrar el perfil."
                ),
                "expected_impact": "Habilitar análisis de brechas y recomendaciones objetivas.",
                "confidence": "high",
                "generated_by": "rules",
            }
        )

    # R7: Muchos descartes con misma razón
    if len(discarded) >= 3:
        discard_reasons = Counter(
            (it.discard_reason or "").strip().lower()
            for it in discarded
            if (it.discard_reason or "").strip()
        )
        top = discard_reasons.most_common(1)
        if top and top[0][1] >= 3:
            reason_text, count = top[0]
            recs.append(
                {
                    "title": f"Recalibrar criterio de descarte: \"{reason_text}\"",
                    "reason": (
                        f"{count} candidatos fueron descartados por la misma razón. "
                        "Vale preguntarse si el criterio es demasiado estricto o si "
                        "el mercado simplemente no lo cumple."
                    ),
                    "expected_impact": "Reducir descartes innecesarios y ampliar la shortlist.",
                    "confidence": "medium",
                    "generated_by": "rules",
                }
            )

    return recs
