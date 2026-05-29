from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate_evaluation import CandidateEvaluation
from app.models.candidate_pipeline_item import CandidatePipelineItem
from app.models.position_spec import PositionSpec
from app.models.search_mandate import SearchMandate
from app.schemas.search_mandate import SearchMandateCreate, SearchMandateUpdate


class SearchMandateService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: SearchMandateCreate) -> SearchMandate:
        mandate = SearchMandate(**payload.model_dump())
        self.db.add(mandate)
        self.db.commit()
        self.db.refresh(mandate)
        return mandate

    def list(self) -> list[SearchMandate]:
        query = select(SearchMandate).order_by(SearchMandate.created_at.desc())
        return list(self.db.scalars(query).all())

    def get(self, mandate_id: int) -> SearchMandate | None:
        return self.db.get(SearchMandate, mandate_id)

    def update(self, mandate: SearchMandate, payload: SearchMandateUpdate) -> SearchMandate:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(mandate, field, value)

        self.db.add(mandate)
        self.db.commit()
        self.db.refresh(mandate)
        return mandate

    def pipeline_count(self, mandate_id: int) -> int:
        query = select(CandidatePipelineItem).where(
            CandidatePipelineItem.mandate_id == mandate_id
        )
        return len(list(self.db.scalars(query).all()))

    def archive(self, mandate: SearchMandate) -> SearchMandate:
        mandate.status = "Archivado"
        self.db.add(mandate)
        self.db.commit()
        self.db.refresh(mandate)
        return mandate

    def delete(self, mandate: SearchMandate) -> None:
        # Cascada manual: pipeline_items, evaluaciones, position_specs, mandato.
        for pipeline_item in list(
            self.db.scalars(
                select(CandidatePipelineItem).where(
                    CandidatePipelineItem.mandate_id == mandate.id
                )
            ).all()
        ):
            self.db.delete(pipeline_item)
        self.db.flush()

        spec_ids = [
            spec.id
            for spec in self.db.scalars(
                select(PositionSpec).where(PositionSpec.search_mandate_id == mandate.id)
            ).all()
        ]
        if spec_ids:
            for evaluation in list(
                self.db.scalars(
                    select(CandidateEvaluation).where(
                        CandidateEvaluation.position_spec_id.in_(spec_ids)
                    )
                ).all()
            ):
                self.db.delete(evaluation)
            self.db.flush()
            for spec in list(
                self.db.scalars(
                    select(PositionSpec).where(PositionSpec.search_mandate_id == mandate.id)
                ).all()
            ):
                self.db.delete(spec)
            self.db.flush()

        self.db.delete(mandate)
        self.db.commit()
