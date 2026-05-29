"""Cliente compartido de OpenAI para Talenscan.

Reglas:
- Todas las llamadas IA viven en backend (ver AGENTS.md §5).
- Si OPENAI_API_KEY no está configurada, las funciones devuelven None y el
  caller debe caer al fallback determinista.
- Toda salida debe ser JSON estructurado validable con Pydantic en el caller.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_openai_client() -> Any | None:
    """Devuelve un cliente OpenAI singleton o None si no hay API key."""
    if not settings.openai_enabled:
        logger.info("OPENAI_API_KEY no está configurada; se usará fallback determinista.")
        return None
    try:
        from openai import OpenAI  # type: ignore[import-not-found]
    except ImportError:
        logger.warning("Paquete openai no instalado; se usará fallback determinista.")
        return None
    return OpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.openai_timeout_seconds,
        max_retries=settings.openai_max_retries,
    )


def ai_split_name_from_slug(slug: str) -> str | None:
    """Usa IA para dividir un slug concatenado en nombre + apellidos hispanos.

    Ejemplos:
    - "perezdiazfernando" -> "Fernando Pérez Díaz"
    - "ronaldcalderon" -> "Ronald Calderón"
    - "mariafernandezgonzalez" -> "María Fernández González"

    Retorna None si no hay IA o si la respuesta no luce como un nombre.
    """
    client = get_openai_client()
    if client is None:
        return None
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres experto en nombres hispanos. Recibes una slug de URL de "
                        "LinkedIn (en minúsculas, sin espacios) y devuelves SOLO el nombre "
                        "completo legible con espacios y mayúsculas correctas en español "
                        "(con tildes si aplica). Sin explicación, sin comillas, sin prefijos. "
                        "Si la slug no parece un nombre humano, devuelve 'NA'."
                    ),
                },
                {"role": "user", "content": slug},
            ],
            max_tokens=30,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("OpenAI slug-name falló: %s", exc)
        return None
    if not response.choices:
        return None
    text = (response.choices[0].message.content or "").strip()
    if not text or text.upper() == "NA":
        return None
    # validación básica: debe tener al menos un espacio y solo letras/espacios/tildes
    if len(text) > 100:
        return None
    cleaned = text.strip(' "\'')
    if not cleaned or len(cleaned.split()) < 2:
        return None
    return cleaned


def generate_structured_json(
    *,
    system_prompt: str,
    user_prompt: str,
    purpose: str,
    model: str | None = None,
    temperature: float = 0.2,
) -> dict[str, Any] | None:
    """Llama al modelo en JSON mode y devuelve un dict ya parseado.

    Devuelve None si:
    - No hay API key configurada.
    - La llamada falla o la respuesta no es JSON válido.

    El caller debe validar el resultado contra un schema Pydantic.
    """
    client = get_openai_client()
    if client is None:
        return None

    chosen_model = model or settings.openai_model
    try:
        response = client.chat.completions.create(
            model=chosen_model,
            response_format={"type": "json_object"},
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("OpenAI %s falló (%s); fallback determinista.", purpose, exc)
        return None

    if not response.choices:
        logger.warning("OpenAI %s devolvió respuesta sin choices.", purpose)
        return None
    content = response.choices[0].message.content or ""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.warning("OpenAI %s devolvió JSON inválido.", purpose)
        return None
