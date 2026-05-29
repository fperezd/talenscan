from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.bulk_evaluation import (
    BulkLinkedInItem,
    BulkLinkedInRequest,
    BulkLinkedInResponse,
)
from app.schemas.candidate_pipeline_item import (
    CandidatePipelineItemCreate,
    CandidatePipelineItemRead,
    CandidatePipelineItemUpdate,
    PipelineReorderPayload,
)
from app.services.bulk_evaluation_service import BulkEvaluationService, parse_linkedin_urls
from app.services.candidate_pipeline_service import CandidatePipelineService
from app.services.candidate_service import CandidateService
from app.services.position_spec_service import PositionSpecService
from app.services.search_mandate_service import SearchMandateService

router = APIRouter(tags=["pipeline"])


def _ensure_mandate(db: Session, mandate_id: int) -> None:
    mandate = SearchMandateService(db).get(mandate_id)
    if mandate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mandato no encontrado")


@router.get(
    "/api/mandatos/{mandate_id}/pipeline",
    response_model=list[CandidatePipelineItemRead],
)
def list_pipeline(mandate_id: int, db: Session = Depends(get_db)) -> list[CandidatePipelineItemRead]:
    _ensure_mandate(db, mandate_id)
    service = CandidatePipelineService(db)
    service.sync_from_evaluations(mandate_id)
    return service.list_by_mandate(mandate_id)


@router.post(
    "/api/mandatos/{mandate_id}/pipeline/items",
    response_model=CandidatePipelineItemRead,
    status_code=status.HTTP_201_CREATED,
)
def create_pipeline_item(
    mandate_id: int,
    payload: CandidatePipelineItemCreate,
    db: Session = Depends(get_db),
) -> CandidatePipelineItemRead:
    _ensure_mandate(db, mandate_id)
    candidate = CandidateService(db).get(payload.candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidato no encontrado")
    service = CandidatePipelineService(db)
    try:
        return service.create(mandate_id=mandate_id, payload=payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.patch(
    "/api/pipeline/items/{item_id}",
    response_model=CandidatePipelineItemRead,
)
def update_pipeline_item(
    item_id: int,
    payload: CandidatePipelineItemUpdate,
    db: Session = Depends(get_db),
) -> CandidatePipelineItemRead:
    service = CandidatePipelineService(db)
    item = service.get(item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ítem de pipeline no encontrado"
        )
    try:
        return service.update(item, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.patch(
    "/api/mandatos/{mandate_id}/pipeline/reorder",
    response_model=list[CandidatePipelineItemRead],
)
def reorder_pipeline(
    mandate_id: int,
    payload: PipelineReorderPayload,
    db: Session = Depends(get_db),
) -> list[CandidatePipelineItemRead]:
    _ensure_mandate(db, mandate_id)
    service = CandidatePipelineService(db)
    try:
        return service.reorder(mandate_id, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get(
    "/api/mandatos/{mandate_id}/shortlist",
    response_model=list[CandidatePipelineItemRead],
)
def shortlist(mandate_id: int, db: Session = Depends(get_db)) -> list[CandidatePipelineItemRead]:
    _ensure_mandate(db, mandate_id)
    service = CandidatePipelineService(db)
    return service.shortlist(mandate_id)


@router.delete("/api/pipeline/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pipeline_item(item_id: int, db: Session = Depends(get_db)) -> None:
    service = CandidatePipelineService(db)
    item = service.get(item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ítem de pipeline no encontrado"
        )
    db.delete(item)
    db.commit()


@router.post(
    "/api/mandatos/{mandate_id}/candidatos-desde-linkedin",
    response_model=BulkLinkedInResponse,
    status_code=status.HTTP_201_CREATED,
)
def bulk_candidates_from_linkedin(
    mandate_id: int,
    payload: BulkLinkedInRequest,
    db: Session = Depends(get_db),
) -> BulkLinkedInResponse:
    _ensure_mandate(db, mandate_id)

    # Aceptamos dos formatos:
    # - urls_text: texto libre del cual se parsean URLs (sin profile_text)
    # - entries: lista estructurada [{url, profile_text}] (con texto del perfil)
    parsed: list[tuple[str, str | None]] = []
    if payload.entries:
        for entry in payload.entries:
            urls_in_entry = parse_linkedin_urls(entry.url)
            for url in urls_in_entry:
                parsed.append((url, entry.profile_text))
    if payload.urls_text:
        for url in parse_linkedin_urls(payload.urls_text):
            parsed.append((url, None))

    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se detectaron URLs válidas de LinkedIn.",
        )

    position_spec = None
    if payload.position_spec_id is not None:
        position_spec = PositionSpecService(db).get(payload.position_spec_id)
        if position_spec is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil objetivo no encontrado",
            )
        if position_spec.search_mandate_id != mandate_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El perfil objetivo no pertenece a este mandato",
            )

    bulk_service = BulkEvaluationService(db)
    items: list[BulkLinkedInItem] = []
    for url, profile_text in parsed:
        result = bulk_service.process_linkedin_url(
            mandate_id=mandate_id,
            url=url,
            position_spec=position_spec,
            profile_text=profile_text,
        )
        items.append(BulkLinkedInItem(**result.__dict__))
    return BulkLinkedInResponse(
        items=items,
        total=len(items),
        created_count=sum(1 for r in items if r.status == "created"),
        duplicate_count=sum(1 for r in items if r.status == "duplicate"),
        error_count=sum(1 for r in items if r.status == "error"),
    )
