"""Detector determinístico de brechas repetidas en evaluaciones 360.

Input:
- list[CandidateEvaluation] del pipeline de un mandato

Output:
- list[dict] listo para persistir como MarketGap

Lógica:
- Cada evaluación tiene `critical_gaps: list[dict]` con shape
  `{requirement, reason, impact, evidence}`.
- Agrupamos por `requirement` (normalizado), contamos frecuencia, calculamos
  impact dominante (high > medium > low por mayoría), generamos evidencia
  citando las primeras 2 razones únicas.
- Solo registramos brechas con frequency >= 2 (deja de ser anecdótico) o
  cuando la única evaluación disponible es de un candidato que repite la
  misma brecha (en cuyo caso aún tiene sentido mostrarla).
"""

from __future__ import annotations

import unicodedata
from collections import Counter, defaultdict
from typing import Any, Iterable

from app.models.candidate_evaluation import CandidateEvaluation


_IMPACT_ORDER = {"high": 3, "medium": 2, "low": 1, "": 0}


def _normalize(value: str | None) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    # Quitar acentos para agrupar mejor "ingles" vs "inglés"
    decomposed = unicodedata.normalize("NFKD", text)
    no_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return no_accents.casefold()


def _impact_winner(impacts: list[str]) -> str:
    if not impacts:
        return "medium"
    counter = Counter(i.lower() for i in impacts if i)
    # Empate → gana el de mayor severidad
    sorted_impacts = sorted(
        counter.items(),
        key=lambda kv: (kv[1], _IMPACT_ORDER.get(kv[0], 0)),
        reverse=True,
    )
    return sorted_impacts[0][0] if sorted_impacts else "medium"


def _recommendation_for(requirement: str, frequency: int, total: int) -> str:
    pct = (frequency / total) * 100 if total > 0 else 0
    req_lower = (requirement or "").lower()
    if "ingles" in req_lower or "inglés" in req_lower or "english" in req_lower:
        return (
            "Validar si el inglés es realmente imprescindible o si puede pasar a "
            "deseable. Alternativa: aceptar candidatos con inglés intermedio que "
            "estén dispuestos a certificar."
        )
    if "lider" in req_lower or "liderazgo" in req_lower or "equipo" in req_lower:
        return (
            "Validar liderazgo en entrevista con casos concretos y pedir "
            "referencias específicas. Considerar candidatos con menor tamaño de "
            "equipo pero alto impacto demostrable."
        )
    if "renta" in req_lower or "salario" in req_lower or "compensaci" in req_lower:
        return "Revisar rango de renta con el cliente. El mercado parece estar fuera del rango."
    if "industria" in req_lower or "sector" in req_lower:
        return (
            "Ampliar a industrias adyacentes con procesos similares. La brecha de "
            "industria específica se repite y limita el mercado."
        )
    if "experiencia" in req_lower or "años" in req_lower or "anos" in req_lower:
        return (
            "Revisar si la cantidad de años requerida es realmente necesaria o si "
            "el calce funcional puede compensar."
        )
    if pct >= 50:
        return (
            f"Brecha repetida en el {int(pct)}% de los candidatos evaluados. "
            "Revisar con el cliente si el requisito puede flexibilizarse."
        )
    return "Validar en entrevista y confirmar criticidad del requisito con el cliente."


def detect_gaps(
    evaluations: Iterable[CandidateEvaluation],
) -> list[dict[str, Any]]:
    evaluations_list = list(evaluations)
    total = len(evaluations_list)
    if total == 0:
        return []

    # Mapa: requirement_normalized -> {"label": str, "impacts": [...], "evidences": set, "count": int}
    groups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"label": "", "impacts": [], "evidences": [], "count": 0}
    )

    for ev in evaluations_list:
        gaps = ev.critical_gaps or []
        if not isinstance(gaps, list):
            continue
        seen_in_this_eval: set[str] = set()
        for raw in gaps:
            if not isinstance(raw, dict):
                continue
            requirement = str(raw.get("requirement") or "").strip()
            if not requirement:
                continue
            key = _normalize(requirement)
            if key in seen_in_this_eval:
                continue  # no contar dos veces dentro de la misma evaluación
            seen_in_this_eval.add(key)
            entry = groups[key]
            # Usar el label más largo encontrado (suele ser el más descriptivo)
            if len(requirement) > len(entry["label"]):
                entry["label"] = requirement
            entry["count"] += 1
            impact_value = str(raw.get("impact") or "").strip()
            if impact_value:
                entry["impacts"].append(impact_value)
            reason = str(raw.get("reason") or "").strip()
            if reason and reason not in entry["evidences"] and len(entry["evidences"]) < 3:
                entry["evidences"].append(reason)

    # Filtrar y armar output
    output: list[dict[str, Any]] = []
    threshold = 2 if total >= 3 else 1  # con muy pocas evals aceptamos freq=1
    for entry in groups.values():
        if entry["count"] < threshold:
            continue
        impact = _impact_winner(entry["impacts"])
        # Mapear texto del impacto al enum esperado
        impact_norm = (
            "high"
            if impact in ("high", "alto", "alta")
            else "low"
            if impact in ("low", "bajo", "baja")
            else "medium"
        )
        evidence = " · ".join(entry["evidences"]) if entry["evidences"] else None
        output.append(
            {
                "title": entry["label"],
                "frequency": entry["count"],
                "total_evaluated": total,
                "impact": impact_norm,
                "evidence": evidence,
                "recommendation": _recommendation_for(
                    entry["label"], entry["count"], total
                ),
            }
        )
    # Ordenar por frecuencia desc → impact severity desc
    output.sort(
        key=lambda d: (d["frequency"], _IMPACT_ORDER.get(d["impact"], 0)),
        reverse=True,
    )
    return output
