from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.document_processing.text_extractor import SUPPORTED_EXTENSIONS, extract_text_from_document
from app.models.candidate_document import CandidateDocument


class CandidateDocumentService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def validate_file(self, file_name: str, file_size: int) -> None:
        extension = Path(file_name).suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError("Formato no soportado. Usa PDF, DOCX o DOC.")

        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if file_size > max_bytes:
            raise ValueError(f"El archivo supera el maximo permitido de {settings.max_upload_size_mb} MB.")

    def create_document(self, candidate_id: int, file_name: str, file_size: int, content: bytes) -> CandidateDocument:
        self.validate_file(file_name=file_name, file_size=file_size)
        raw_text, extraction_status = extract_text_from_document(file_name=file_name, content=content)

        item = CandidateDocument(
            candidate_id=candidate_id,
            file_name=file_name,
            file_type=Path(file_name).suffix.lower().replace(".", ""),
            file_size=file_size,
            file_url=f"{settings.storage_base_url}/{candidate_id}/{file_name}",
            raw_text=raw_text,
            text_extraction_status=extraction_status,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_by_candidate(self, candidate_id: int) -> list[CandidateDocument]:
        query = (
            select(CandidateDocument)
            .where(CandidateDocument.candidate_id == candidate_id)
            .order_by(CandidateDocument.uploaded_at.desc())
        )
        return list(self.db.scalars(query).all())

    def get(self, document_id: int) -> CandidateDocument | None:
        return self.db.get(CandidateDocument, document_id)

    def save(self, item: CandidateDocument) -> CandidateDocument:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item
