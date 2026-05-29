from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.schemas.candidate import CandidateCreate, CandidateUpdate


class CandidateService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: CandidateCreate) -> Candidate:
        item = Candidate(**payload.model_dump())
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def list(self) -> list[Candidate]:
        query = select(Candidate).order_by(Candidate.created_at.desc())
        return list(self.db.scalars(query).all())

    def get(self, candidate_id: int) -> Candidate | None:
        return self.db.get(Candidate, candidate_id)

    def update(self, item: Candidate, payload: CandidateUpdate) -> Candidate:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item
