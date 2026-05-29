from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.candidate_pipeline_item import CandidatePipelineItem
from app.schemas.bulk_evaluation import BulkEvaluationItem, BulkEvaluationResponse
from app.schemas.candidate_evaluation import CandidateEvaluationCreate, CandidateEvaluationRead
from app.services.bulk_evaluation_service import BulkEvaluationService
from app.services.candidate_evaluation_service import CandidateEvaluationService
from app.services.candidate_service import CandidateService
from app.services.position_spec_service import PositionSpecService
from app.services.search_mandate_service import SearchMandateService

router = APIRouter(tags=["evaluaciones"])


@router.post("/api/evaluaciones", response_model=CandidateEvaluationRead, status_code=status.HTTP_201_CREATED)
def create_evaluation(payload: CandidateEvaluationCreate, db: Session = Depends(get_db)) -> CandidateEvaluationRead:
    candidate_service = CandidateService(db)
    candidate = candidate_service.get(payload.candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidato no encontrado")

    position_spec_service = PositionSpecService(db)
    position_spec = position_spec_service.get(payload.position_spec_id)
    if position_spec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil objetivo no encontrado")

    service = CandidateEvaluationService(db)
    try:
        return service.create(candidate_id=payload.candidate_id, position_spec=position_spec)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/api/evaluaciones", response_model=list[CandidateEvaluationRead])
def list_evaluations(db: Session = Depends(get_db)) -> list[CandidateEvaluationRead]:
    service = CandidateEvaluationService(db)
    return service.list_all()


@router.get("/api/evaluaciones/{evaluation_id}", response_model=CandidateEvaluationRead)
def get_evaluation(evaluation_id: int, db: Session = Depends(get_db)) -> CandidateEvaluationRead:
    service = CandidateEvaluationService(db)
    item = service.get(evaluation_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluacion no encontrada")
    return item


@router.get("/api/perfiles-objetivo/{position_spec_id}/evaluaciones", response_model=list[CandidateEvaluationRead])
def list_evaluations_by_position_spec(
    position_spec_id: int, db: Session = Depends(get_db)
) -> list[CandidateEvaluationRead]:
    service = CandidateEvaluationService(db)
    return service.list_by_position_spec(position_spec_id)


@router.get("/api/candidatos/{candidate_id}/evaluaciones", response_model=list[CandidateEvaluationRead])
def list_evaluations_by_candidate(candidate_id: int, db: Session = Depends(get_db)) -> list[CandidateEvaluationRead]:
    service = CandidateEvaluationService(db)
    return service.list_by_candidate(candidate_id)


@router.delete("/api/evaluaciones/{evaluation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evaluation(evaluation_id: int, db: Session = Depends(get_db)) -> None:
    service = CandidateEvaluationService(db)
    item = service.get(evaluation_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evaluación no encontrada"
        )

    pipeline_items = list(
        db.scalars(
            select(CandidatePipelineItem).where(
                CandidatePipelineItem.evaluation_id == evaluation_id
            )
        ).all()
    )
    for pipeline_item in pipeline_items:
        db.delete(pipeline_item)
    db.flush()
    db.delete(item)
    db.commit()


@router.post(
    "/api/mandatos/{mandate_id}/evaluaciones-bulk",
    response_model=BulkEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def bulk_evaluate_candidates(
    mandate_id: int,
    position_spec_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
) -> BulkEvaluationResponse:
    mandate = SearchMandateService(db).get(mandate_id)
    if mandate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mandato no encontrado")

    position_spec = PositionSpecService(db).get(position_spec_id)
    if position_spec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Perfil objetivo no encontrado"
        )
    if position_spec.search_mandate_id != mandate_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El perfil objetivo no pertenece a este mandato",
        )

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No se enviaron archivos"
        )

    bulk_service = BulkEvaluationService(db)
    results: list[BulkEvaluationItem] = []
    for upload in files:
        content = await upload.read()
        if not content:
            results.append(
                BulkEvaluationItem(
                    file_name=upload.filename or "documento",
                    status="error",
                    error="Archivo vacío",
                )
            )
            continue
        outcome = bulk_service.process_one(
            mandate_id=mandate_id,
            position_spec=position_spec,
            file_name=upload.filename or "documento",
            file_content=content,
        )
        results.append(BulkEvaluationItem(**outcome.__dict__))

    return BulkEvaluationResponse(
        items=results,
        total=len(results),
        created_count=sum(1 for r in results if r.status == "created"),
        duplicate_count=sum(1 for r in results if r.status == "duplicate"),
        error_count=sum(1 for r in results if r.status == "error"),
    )
