from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.candidate_document import CandidateDocument
from app.models.candidate_evaluation import CandidateEvaluation
from app.models.candidate_pipeline_item import CandidatePipelineItem
from app.models.candidate_profile import CandidateProfile
from app.schemas.candidate import CandidateCreate, CandidateRead, CandidateUpdate
from app.schemas.candidate_document import CandidateDocumentRead
from app.schemas.candidate_profile import CandidateProfileRead
from app.services.candidate_document_service import CandidateDocumentService
from app.services.candidate_profile_service import CandidateProfileService
from app.services.candidate_service import CandidateService

router = APIRouter(tags=["candidatos"])


@router.post("/api/candidatos", response_model=CandidateRead, status_code=status.HTTP_201_CREATED)
def create_candidate(payload: CandidateCreate, db: Session = Depends(get_db)) -> CandidateRead:
    service = CandidateService(db)
    return service.create(payload)


@router.get("/api/candidatos", response_model=list[CandidateRead])
def list_candidates(db: Session = Depends(get_db)) -> list[CandidateRead]:
    service = CandidateService(db)
    return service.list()


@router.get("/api/candidatos/{candidate_id}", response_model=CandidateRead)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)) -> CandidateRead:
    service = CandidateService(db)
    item = service.get(candidate_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidato no encontrado")
    return item


@router.put("/api/candidatos/{candidate_id}", response_model=CandidateRead)
def update_candidate(candidate_id: int, payload: CandidateUpdate, db: Session = Depends(get_db)) -> CandidateRead:
    service = CandidateService(db)
    item = service.get(candidate_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidato no encontrado")
    return service.update(item, payload)


@router.delete("/api/candidatos/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(candidate_id: int, db: Session = Depends(get_db)) -> None:
    service = CandidateService(db)
    candidate = service.get(candidate_id)
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Candidato no encontrado"
        )

    # Borra cascada manual: pipeline items → evaluaciones → perfiles → documentos → candidato.
    # flush() entre cada nivel para que el ORDEN del SQL emitido respete los FKs.
    for pipeline_item in list(
        db.scalars(
            select(CandidatePipelineItem).where(CandidatePipelineItem.candidate_id == candidate_id)
        ).all()
    ):
        db.delete(pipeline_item)
    db.flush()

    for evaluation in list(
        db.scalars(
            select(CandidateEvaluation).where(CandidateEvaluation.candidate_id == candidate_id)
        ).all()
    ):
        db.delete(evaluation)
    db.flush()

    for profile in list(
        db.scalars(
            select(CandidateProfile).where(CandidateProfile.candidate_id == candidate_id)
        ).all()
    ):
        db.delete(profile)
    db.flush()

    for document in list(
        db.scalars(
            select(CandidateDocument).where(CandidateDocument.candidate_id == candidate_id)
        ).all()
    ):
        db.delete(document)
    db.flush()

    db.delete(candidate)
    db.commit()


@router.post(
    "/api/candidatos/{candidate_id}/documentos",
    response_model=CandidateDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_candidate_document(
    candidate_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)
) -> CandidateDocumentRead:
    candidate_service = CandidateService(db)
    candidate = candidate_service.get(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidato no encontrado")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo vacio")

    service = CandidateDocumentService(db)
    try:
        item = service.create_document(
            candidate_id=candidate_id,
            file_name=file.filename or "documento",
            file_size=len(payload),
            content=payload,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return item


@router.get("/api/candidatos/{candidate_id}/documentos", response_model=list[CandidateDocumentRead])
def list_candidate_documents(candidate_id: int, db: Session = Depends(get_db)) -> list[CandidateDocumentRead]:
    candidate_service = CandidateService(db)
    candidate = candidate_service.get(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidato no encontrado")

    service = CandidateDocumentService(db)
    return service.list_by_candidate(candidate_id)


@router.post(
    "/api/documentos-candidato/{document_id}/generar-perfil",
    response_model=CandidateProfileRead,
    status_code=status.HTTP_201_CREATED,
)
def generate_candidate_profile(document_id: int, db: Session = Depends(get_db)) -> CandidateProfileRead:
    document_service = CandidateDocumentService(db)
    profile_service = CandidateProfileService(db)
    candidate_service = CandidateService(db)

    document = document_service.get(document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado")

    candidate = candidate_service.get(document.candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidato no encontrado")

    existing = profile_service.get_by_document(document_id)
    if existing is not None:
        return existing

    try:
        profile = profile_service.create_from_document(candidate, document)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return profile


@router.get("/api/candidatos/{candidate_id}/perfiles", response_model=list[CandidateProfileRead])
def list_candidate_profiles(candidate_id: int, db: Session = Depends(get_db)) -> list[CandidateProfileRead]:
    candidate_service = CandidateService(db)
    candidate = candidate_service.get(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidato no encontrado")

    profile_service = CandidateProfileService(db)
    return profile_service.list_by_candidate(candidate_id)
