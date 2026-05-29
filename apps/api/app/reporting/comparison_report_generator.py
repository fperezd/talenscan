"""Genera el PDF del informe comparativo (WeasyPrint + HTML template)."""

from __future__ import annotations

from typing import Any

from jinja2 import Template

from app.reporting.comparison_html_template import COMPARISON_HTML_TEMPLATE


def build_comparison_pdf(context: dict[str, Any]) -> bytes:
    rendered = Template(COMPARISON_HTML_TEMPLATE).render(**context)
    # Lazy import: WeasyPrint requiere libs nativas no disponibles en todos los
    # entornos de desarrollo. Solo este endpoint específico falla si faltan.
    from weasyprint import HTML  # type: ignore[import-not-found]

    return HTML(string=rendered).write_pdf()
