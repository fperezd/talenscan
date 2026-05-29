"""Orquestador de carga masiva de CVs.

Recibe N archivos, los procesa secuencialmente (extracción + perfil + evaluación)
y los deja en el pipeline del mandato en stage='evaluated'. Detecta duplicados
por nombre normalizado del candidato dentro del mismo mandato.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.candidate_profile_parser import enrich_candidate_contact, parse_candidate_profile
from app.ai.linkedin_apify import (
    apify_to_candidate_payload,
    apify_to_full_profile,
    fetch_linkedin_profile as fetch_linkedin_profile_apify,
)
from app.ai.openai_client import ai_split_name_from_slug
from app.core.config import settings
from app.models.candidate import Candidate
from app.models.candidate_document import CandidateDocument
from app.models.candidate_pipeline_item import CandidatePipelineItem
from app.models.candidate_profile import CandidateProfile
from app.models.position_spec import PositionSpec
from app.services.candidate_document_service import CandidateDocumentService
from app.services.candidate_evaluation_service import CandidateEvaluationService
from app.services.candidate_pipeline_service import CandidatePipelineService
from app.services.candidate_profile_service import CandidateProfileService

logger = logging.getLogger(__name__)


def _normalize_name(value: str) -> str:
    """Normaliza para comparación: minúsculas, sin acentos, espacios colapsados."""
    decomposed = unicodedata.normalize("NFKD", value)
    no_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", no_accents.lower()).strip()


def candidate_name_from_filename(file_name: str) -> str:
    """Extrae un nombre legible del nombre de archivo.

    "Ronald_Calderon_CV.pdf"      -> "Ronald Calderon"
    "CV - Maria Lopez.docx"       -> "Maria Lopez"
    "12345-juan.perez-cv.PDF"     -> "Juan Perez"
    "candidato.pdf"               -> "Candidato"
    """
    stem = Path(file_name).stem
    cleaned = re.sub(
        r"\b(cv|curriculum|curr[ií]culum|resume|talenscan|evaluaci[oó]n|perfil)\b",
        " ",
        stem,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"[_\-\.]+", " ", cleaned)
    cleaned = re.sub(r"\d+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return "Candidato sin nombre"
    return " ".join(word.capitalize() for word in cleaned.split())


def candidate_name_from_linkedin(url: str) -> str:
    """Extrae un nombre tentativo desde una URL de LinkedIn.

    https://www.linkedin.com/in/ronald-calderon-abc123/  -> "Ronald Calderon"
    https://linkedin.com/in/maria.lopez                 -> "Maria Lopez"
    https://linkedin.com/in/perezdiazfernando            -> usa IA para "Fernando Pérez Díaz"
    """
    match = re.search(r"linkedin\.com/(?:in|pub|profile)/([^/?#]+)", url, flags=re.IGNORECASE)
    if not match:
        return "Candidato LinkedIn"
    slug = match.group(1)
    slug = re.sub(r"-[a-z0-9]{6,}$", "", slug, flags=re.IGNORECASE)  # quita hashes finales
    cleaned = re.sub(r"[._\-]+", " ", slug)
    cleaned = re.sub(r"\d+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return "Candidato LinkedIn"
    parts = cleaned.split()
    deterministic = " ".join(word.capitalize() for word in parts)

    # Si el slug viene como una sola palabra concatenada (p.ej. "perezdiazfernando"),
    # la regex no puede partirla. Pedimos a la IA que lo divida en nombre hispano.
    if len(parts) == 1 and len(parts[0]) >= 8:
        ai_name = ai_split_name_from_slug(parts[0])
        if ai_name:
            return ai_name
    return deterministic


def parse_linkedin_urls(raw_text: str) -> list[str]:
    """Encuentra URLs de LinkedIn en un bloque de texto libre."""
    pattern = re.compile(
        r"(https?://)?(www\.)?linkedin\.com/(?:in|pub|profile)/[A-Za-z0-9._\-%]+/?",
        flags=re.IGNORECASE,
    )
    seen: set[str] = set()
    urls: list[str] = []
    for match in pattern.finditer(raw_text or ""):
        url = match.group(0)
        if not url.startswith("http"):
            url = "https://" + url.lstrip("/")
        url = url.rstrip("/")
        normalized = url.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        urls.append(url)
    return urls


@dataclass
class BulkUploadResult:
    file_name: str
    status: Literal["created", "duplicate", "error"]
    candidate_id: int | None = None
    candidate_name: str | None = None
    evaluation_id: int | None = None
    pipeline_item_id: int | None = None
    error: str | None = None


@dataclass
class BulkLinkedInResult:
    url: str
    status: Literal["created", "duplicate", "error"]
    candidate_id: int | None = None
    candidate_name: str | None = None
    pipeline_item_id: int | None = None
    error: str | None = None


class BulkEvaluationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _existing_candidate_in_mandate(
        self, mandate_id: int, normalized_name: str
    ) -> Candidate | None:
        query = (
            select(Candidate)
            .join(CandidatePipelineItem, CandidatePipelineItem.candidate_id == Candidate.id)
            .where(CandidatePipelineItem.mandate_id == mandate_id)
        )
        for candidate in self.db.scalars(query).all():
            if _normalize_name(candidate.full_name) == normalized_name:
                return candidate
        return None

    def process_one(
        self,
        *,
        mandate_id: int,
        position_spec: PositionSpec,
        file_name: str,
        file_content: bytes,
    ) -> BulkUploadResult:
        document_service = CandidateDocumentService(self.db)
        try:
            document_service.validate_file(file_name=file_name, file_size=len(file_content))
        except ValueError as error:
            return BulkUploadResult(file_name=file_name, status="error", error=str(error))

        derived_name = candidate_name_from_filename(file_name)
        normalized = _normalize_name(derived_name)

        existing = self._existing_candidate_in_mandate(mandate_id, normalized)
        if existing is not None:
            return BulkUploadResult(
                file_name=file_name,
                status="duplicate",
                candidate_id=existing.id,
                candidate_name=existing.full_name,
            )

        try:
            candidate = Candidate(full_name=derived_name)
            self.db.add(candidate)
            self.db.flush()  # need id before document

            document = document_service.create_document(
                candidate_id=candidate.id,
                file_name=file_name,
                file_size=len(file_content),
                content=file_content,
            )

            if document.raw_text:
                enrich_candidate_contact(candidate, document.raw_text)
                self.db.add(candidate)

            profile_service = CandidateProfileService(self.db)
            profile_service.create_from_document(candidate=candidate, document=document)

            evaluation_service = CandidateEvaluationService(self.db)
            evaluation = evaluation_service.create(
                candidate_id=candidate.id, position_spec=position_spec
            )

            pipeline_service = CandidatePipelineService(self.db)
            existing_item = pipeline_service.get_by_candidate(
                mandate_id=mandate_id, candidate_id=candidate.id
            )
            if existing_item is None:
                pipeline_item = CandidatePipelineItem(
                    mandate_id=mandate_id,
                    candidate_id=candidate.id,
                    evaluation_id=evaluation.id,
                    stage="evaluated",
                    stage_order=pipeline_service._next_order(mandate_id, "evaluated"),
                )
                self.db.add(pipeline_item)
                self.db.commit()
                self.db.refresh(pipeline_item)
            else:
                existing_item.evaluation_id = evaluation.id
                existing_item.stage = "evaluated"
                self.db.add(existing_item)
                self.db.commit()
                self.db.refresh(existing_item)
                pipeline_item = existing_item

            return BulkUploadResult(
                file_name=file_name,
                status="created",
                candidate_id=candidate.id,
                candidate_name=candidate.full_name,
                evaluation_id=evaluation.id,
                pipeline_item_id=pipeline_item.id,
            )
        except Exception as error:  # noqa: BLE001
            self.db.rollback()
            logger.exception("Error procesando %s", file_name)
            return BulkUploadResult(file_name=file_name, status="error", error=str(error))

    def process_linkedin_url(
        self,
        *,
        mandate_id: int,
        url: str,
        position_spec: "PositionSpec | None" = None,
        profile_text: str | None = None,
    ) -> BulkLinkedInResult:
        """Crea candidato + pipeline item desde una URL de LinkedIn.

        - Valida la URL y extrae nombre tentativo del slug.
        - Crea candidato con linkedin_url guardada.
        - Si position_spec se entrega: crea perfil estructurado placeholder
          (con metadatos de origen) y genera Evaluación 360 que cae en
          'evaluated'. Si no, el item queda en 'received' (CV pendiente).
        """
        # Si Apify está disponible, intenta enriquecer con datos reales del perfil.
        scraper_data = None
        scraper_payload = None
        scraper_profile = None
        if settings.apify_enabled:
            scraper_data = fetch_linkedin_profile_apify(url)
            if scraper_data:
                scraper_payload = apify_to_candidate_payload(scraper_data)
                scraper_profile = apify_to_full_profile(scraper_data)

        derived_name = (
            scraper_payload.get("full_name") if scraper_payload else candidate_name_from_linkedin(url)
        )
        normalized = _normalize_name(derived_name or "")

        existing = self._existing_candidate_in_mandate(mandate_id, normalized)
        if existing is not None:
            return BulkLinkedInResult(
                url=url,
                status="duplicate",
                candidate_id=existing.id,
                candidate_name=existing.full_name,
            )

        try:
            candidate = Candidate(full_name=derived_name, linkedin_url=url)
            if scraper_payload:
                candidate.current_position = scraper_payload.get("current_position")
                candidate.current_company = scraper_payload.get("current_company")
                candidate.country = scraper_payload.get("country")
                candidate.email = scraper_payload.get("email")
                candidate.phone = scraper_payload.get("phone")
            self.db.add(candidate)
            self.db.flush()

            pipeline_service = CandidatePipelineService(self.db)
            stage = "received"
            evaluation_id: int | None = None

            if position_spec is not None:
                # Prioridad para construir el perfil estructurado:
                # 1) texto pegado por el usuario → parser IA
                # 2) datos estructurados de Scrapingdog → mapper directo (sin IA)
                # 3) placeholder mínimo
                clean_profile_text = (profile_text or "").strip()
                if clean_profile_text:
                    # Usuario pegó el contenido del perfil LinkedIn. Lo procesamos
                    # con el parser IA porque viene como texto plano.
                    enrich_candidate_contact(candidate, clean_profile_text)
                    self.db.add(candidate)

                    document = CandidateDocument(
                        candidate_id=candidate.id,
                        file_name=f"linkedin_{candidate.id}.txt",
                        file_type="txt",
                        file_size=len(clean_profile_text.encode("utf-8")),
                        file_url=f"linkedin://{url}",
                        raw_text=clean_profile_text,
                        text_extraction_status="Perfil del candidato generado",
                    )
                    self.db.add(document)
                    self.db.flush()

                    parsed = parse_candidate_profile(candidate, document)
                    profile = CandidateProfile(
                        candidate_id=candidate.id,
                        candidate_document_id=document.id,
                        **parsed,
                    )
                    profile.parsed_json = {
                        **parsed["parsed_json"],
                        "source": "linkedin_url_with_text",
                        "linkedin_url": url,
                    }
                    self.db.add(profile)
                    self.db.flush()
                elif scraper_profile:
                    # Datos estructurados de Scrapingdog → mapper directo. NO pasamos
                    # por IA porque eso destruye el orden y mezcla títulos con descripciones.
                    profile = CandidateProfile(
                        candidate_id=candidate.id,
                        candidate_document_id=None,
                        **{k: v for k, v in scraper_profile.items() if k != "parsed_json"},
                    )
                    profile.parsed_json = {
                        **scraper_profile.get("parsed_json", {}),
                        "linkedin_url": url,
                    }
                    self.db.add(profile)
                    self.db.flush()
                else:
                    # Sin texto del perfil: perfil estructurado mínimo / placeholder.
                    profile = CandidateProfile(
                        candidate_id=candidate.id,
                        candidate_document_id=None,
                        current_position=None,
                        current_company=None,
                        total_years_experience=None,
                        industries=[],
                        roles=[],
                        education=[],
                        certifications=[],
                        tools=[],
                        languages=[],
                        achievements=[],
                        inferred_seniority=None,
                        missing_information=[
                            "No evidenciado en el CV: cargo actual",
                            "No evidenciado en el CV: experiencia detallada",
                            "No evidenciado en el CV: industrias",
                            "Origen del candidato: LinkedIn (sin CV cargado)",
                        ],
                        evidence_snippets=[f"Perfil de LinkedIn: {url}"],
                        parsed_json={
                            "candidate_name": candidate.full_name,
                            "source": "linkedin_url",
                            "linkedin_url": url,
                        },
                    )
                    self.db.add(profile)
                    self.db.flush()

                evaluation_service = CandidateEvaluationService(self.db)
                evaluation = evaluation_service.create(
                    candidate_id=candidate.id, position_spec=position_spec
                )
                evaluation_id = evaluation.id
                stage = "evaluated"

            pipeline_item = CandidatePipelineItem(
                mandate_id=mandate_id,
                candidate_id=candidate.id,
                evaluation_id=evaluation_id,
                stage=stage,
                stage_order=pipeline_service._next_order(mandate_id, stage),
            )
            self.db.add(pipeline_item)
            self.db.commit()
            self.db.refresh(pipeline_item)
            return BulkLinkedInResult(
                url=url,
                status="created",
                candidate_id=candidate.id,
                candidate_name=candidate.full_name,
                pipeline_item_id=pipeline_item.id,
            )
        except Exception as error:  # noqa: BLE001
            self.db.rollback()
            logger.exception("Error procesando LinkedIn %s", url)
            return BulkLinkedInResult(url=url, status="error", error=str(error))
