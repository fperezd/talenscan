"""Generador PDF de Evaluación 360 vía HTML + WeasyPrint.

Mantiene fidelidad visual 1:1 con la pantalla web reutilizando una
plantilla HTML/CSS equivalente. WeasyPrint convierte a PDF respetando
flexbox/tablas/colores.
"""

from __future__ import annotations

from typing import Any

from jinja2 import Template

from app.reporting.html_template import REPORT_HTML_TEMPLATE


def _score_tone(score: int) -> dict[str, str]:
    """Tonos equivalentes a `scoreTone` del componente React."""
    if score >= 85:
        return {
            "ring": "#6EE7B7",
            "bg": "#ECFDF5",
            "text": "#047857",
            "badge_bg": "#D1FAE5",
            "badge_fg": "#047857",
        }
    if score >= 70:
        return {
            "ring": "#93C5FD",
            "bg": "#EFF6FF",
            "text": "#1D4ED8",
            "badge_bg": "#DBEAFE",
            "badge_fg": "#1D4ED8",
        }
    if score >= 55:
        return {
            "ring": "#FCD34D",
            "bg": "#FFFBEB",
            "text": "#B45309",
            "badge_bg": "#FEF3C7",
            "badge_fg": "#B45309",
        }
    if score >= 40:
        return {
            "ring": "#CBD5E1",
            "bg": "#F1F5F9",
            "text": "#475569",
            "badge_bg": "#E2E8F0",
            "badge_fg": "#475569",
        }
    return {
        "ring": "#FDA4AF",
        "bg": "#FFF1F2",
        "text": "#BE123C",
        "badge_bg": "#FFE4E6",
        "badge_fg": "#BE123C",
    }


def _clean_evidence(value: Any) -> str:
    text = str(value or "").strip()
    # Quita markdown headers y comillas residuales.
    while text.startswith(("#", '"', "'", "`")):
        text = text.lstrip("#\"'` ").strip()
    return text


def build_pdf_report(context: dict[str, Any]) -> bytes:
    score = int(context.get("score", 0) or 0)
    tone = _score_tone(score)

    template_context = {
        **context,
        "tone": tone,
        "score": score,
        "evidence": [
            _clean_evidence(item) for item in (context.get("evidence") or []) if str(item).strip()
        ],
    }

    rendered = Template(REPORT_HTML_TEMPLATE).render(**template_context)
    # Lazy import: WeasyPrint requiere libs nativas (GTK/Pango/Cairo) que
    # no siempre están presentes en entornos de desarrollo Windows. La app
    # debe poder arrancar sin ellas; solo este endpoint específico falla
    # cuando WeasyPrint no se puede cargar.
    from weasyprint import HTML  # type: ignore[import-not-found]

    return HTML(string=rendered).write_pdf()
