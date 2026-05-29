from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.candidate_profile_parser import enrich_candidate_contact, parse_candidate_profile
from app.models.candidate import Candidate
from app.models.candidate_document import CandidateDocument
from app.models.candidate_profile import CandidateProfile


class CandidateProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, profile_id: int) -> CandidateProfile | None:
        return self.db.get(CandidateProfile, profile_id)

    def get_by_document(self, document_id: int) -> CandidateProfile | None:
        query = select(CandidateProfile).where(CandidateProfile.candidate_document_id == document_id)
        return self.db.scalars(query).first()

    def list_by_candidate(self, candidate_id: int) -> list[CandidateProfile]:
        query = (
            select(CandidateProfile)
            .where(CandidateProfile.candidate_id == candidate_id)
            .order_by(CandidateProfile.created_at.desc())
        )
        return list(self.db.scalars(query).all())

    def create_from_document(self, candidate: Candidate, document: CandidateDocument) -> CandidateProfile:
        if not document.raw_text:
            raise ValueError("El documento no tiene texto utilizable. Revisa OCR o formato del archivo.")

        parsed = parse_candidate_profile(candidate, document)
        enrich_candidate_contact(candidate, document.raw_text)

        profile = CandidateProfile(
            candidate_id=candidate.id,
            candidate_document_id=document.id,
            **parsed,
        )
        document.text_extraction_status = "Perfil del candidato generado"

        self.db.add(candidate)
        self.db.add(document)
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile
