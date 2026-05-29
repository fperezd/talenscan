from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate_evaluation import CandidateEvaluation
from app.models.candidate_pipeline_item import PIPELINE_STAGES, CandidatePipelineItem
from app.models.position_spec import PositionSpec
from app.schemas.candidate_pipeline_item import (
    CandidatePipelineItemCreate,
    CandidatePipelineItemUpdate,
    PipelineReorderPayload,
)


def _default_stage_for_evaluation(score: int | None) -> str:
    """Toda evaluación termina en 'evaluated' por defecto.

    El consultor decide manualmente si pasarla a preseleccionados,
    presentar al cliente o descartar, vía drag&drop en el Kanban.
    """
    return "evaluated"


class CandidatePipelineService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_mandate(self, mandate_id: int) -> list[CandidatePipelineItem]:
        query = (
            select(CandidatePipelineItem)
            .where(CandidatePipelineItem.mandate_id == mandate_id)
            .order_by(CandidatePipelineItem.stage_order.asc(), CandidatePipelineItem.created_at.asc())
        )
        return list(self.db.scalars(query).all())

    def get(self, item_id: int) -> CandidatePipelineItem | None:
        return self.db.get(CandidatePipelineItem, item_id)

    def _next_order(self, mandate_id: int, stage: str) -> int:
        query = select(CandidatePipelineItem.stage_order).where(
            CandidatePipelineItem.mandate_id == mandate_id,
            CandidatePipelineItem.stage == stage,
        )
        existing = [value for value in self.db.scalars(query).all()]
        return (max(existing) + 1) if existing else 0

    def get_by_candidate(self, mandate_id: int, candidate_id: int) -> CandidatePipelineItem | None:
        query = select(CandidatePipelineItem).where(
            CandidatePipelineItem.mandate_id == mandate_id,
            CandidatePipelineItem.candidate_id == candidate_id,
        )
        return self.db.scalars(query).first()

    def create(self, mandate_id: int, payload: CandidatePipelineItemCreate) -> CandidatePipelineItem:
        if payload.stage not in PIPELINE_STAGES:
            raise ValueError("Etapa de pipeline no válida")

        existing = self.get_by_candidate(mandate_id=mandate_id, candidate_id=payload.candidate_id)
        if existing is not None:
            return existing

        item = CandidatePipelineItem(
            mandate_id=mandate_id,
            candidate_id=payload.candidate_id,
            evaluation_id=payload.evaluation_id,
            stage=payload.stage,
            stage_order=self._next_order(mandate_id, payload.stage),
            is_priority=payload.is_priority,
            is_shortlisted=payload.is_shortlisted,
            consultant_notes=payload.consultant_notes,
            tags=list(payload.tags),
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def sync_from_evaluations(self, mandate_id: int) -> list[CandidatePipelineItem]:
        evaluations_query = (
            select(CandidateEvaluation)
            .join(PositionSpec, CandidateEvaluation.position_spec_id == PositionSpec.id)
            .where(PositionSpec.search_mandate_id == mandate_id)
            .order_by(CandidateEvaluation.created_at.asc())
        )
        evaluations = list(self.db.scalars(evaluations_query).all())
        for evaluation in evaluations:
            existing = self.get_by_candidate(mandate_id=mandate_id, candidate_id=evaluation.candidate_id)
            if existing is not None:
                if existing.evaluation_id != evaluation.id:
                    existing.evaluation_id = evaluation.id
                    self.db.add(existing)
                continue
            stage = _default_stage_for_evaluation(evaluation.total_score)
            item = CandidatePipelineItem(
                mandate_id=mandate_id,
                candidate_id=evaluation.candidate_id,
                evaluation_id=evaluation.id,
                stage=stage,
                stage_order=self._next_order(mandate_id, stage),
            )
            self.db.add(item)
        self.db.commit()
        return self.list_by_mandate(mandate_id)

    def update(
        self, item: CandidatePipelineItem, payload: CandidatePipelineItemUpdate
    ) -> CandidatePipelineItem:
        data = payload.model_dump(exclude_unset=True)
        moved = False
        if "stage" in data and data["stage"] is not None and data["stage"] != item.stage:
            if data["stage"] not in PIPELINE_STAGES:
                raise ValueError("Etapa de pipeline no válida")
            item.stage = data["stage"]
            moved = True
            if "stage_order" not in data:
                data["stage_order"] = self._next_order(item.mandate_id, data["stage"])
        for field in (
            "stage_order",
            "is_priority",
            "is_shortlisted",
            "consultant_notes",
            "discard_reason",
        ):
            if field in data and data[field] is not None:
                setattr(item, field, data[field])
        if "tags" in data and data["tags"] is not None:
            item.tags = list(data["tags"])
        if moved:
            item.last_moved_at = datetime.now(timezone.utc)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def reorder(self, mandate_id: int, payload: PipelineReorderPayload) -> list[CandidatePipelineItem]:
        ids = [entry.id for entry in payload.items]
        if not ids:
            return self.list_by_mandate(mandate_id)
        query = select(CandidatePipelineItem).where(
            CandidatePipelineItem.mandate_id == mandate_id,
            CandidatePipelineItem.id.in_(ids),
        )
        items_by_id = {item.id: item for item in self.db.scalars(query).all()}
        now = datetime.now(timezone.utc)
        for entry in payload.items:
            item = items_by_id.get(entry.id)
            if item is None:
                continue
            if entry.stage not in PIPELINE_STAGES:
                raise ValueError("Etapa de pipeline no válida")
            if item.stage != entry.stage:
                item.stage = entry.stage
                item.last_moved_at = now
            item.stage_order = entry.stage_order
            self.db.add(item)
        self.db.commit()
        return self.list_by_mandate(mandate_id)

    def shortlist(self, mandate_id: int) -> list[CandidatePipelineItem]:
        query = (
            select(CandidatePipelineItem)
            .where(
                CandidatePipelineItem.mandate_id == mandate_id,
                CandidatePipelineItem.stage.in_(("preselected", "present_to_client")),
            )
            .order_by(CandidatePipelineItem.stage_order.asc())
        )
        return list(self.db.scalars(query).all())
