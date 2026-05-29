from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.search_mandate import SearchMandateCreate, SearchMandateRead, SearchMandateUpdate
from app.services.search_mandate_service import SearchMandateService

router = APIRouter(prefix="/api/mandatos", tags=["mandatos"])


@router.post("", response_model=SearchMandateRead, status_code=status.HTTP_201_CREATED)
def create_mandate(payload: SearchMandateCreate, db: Session = Depends(get_db)) -> SearchMandateRead:
    service = SearchMandateService(db)
    return service.create(payload)


@router.get("", response_model=list[SearchMandateRead])
def list_mandates(db: Session = Depends(get_db)) -> list[SearchMandateRead]:
    service = SearchMandateService(db)
    return service.list()


@router.get("/{mandate_id}", response_model=SearchMandateRead)
def get_mandate(mandate_id: int, db: Session = Depends(get_db)) -> SearchMandateRead:
    service = SearchMandateService(db)
    mandate = service.get(mandate_id)
    if mandate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mandato no encontrado")
    return mandate


@router.put("/{mandate_id}", response_model=SearchMandateRead)
def update_mandate(
    mandate_id: int, payload: SearchMandateUpdate, db: Session = Depends(get_db)
) -> SearchMandateRead:
    service = SearchMandateService(db)
    mandate = service.get(mandate_id)
    if mandate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mandato no encontrado")
    return service.update(mandate, payload)


@router.delete("/{mandate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mandate(mandate_id: int, db: Session = Depends(get_db)) -> None:
    service = SearchMandateService(db)
    mandate = service.get(mandate_id)
    if mandate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mandato no encontrado")
    if service.pipeline_count(mandate_id) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "El mandato tiene candidatos en pipeline. Usa archivar en lugar de eliminar "
                "para preservar la trazabilidad."
            ),
        )
    service.delete(mandate)


@router.post("/{mandate_id}/archivar", response_model=SearchMandateRead)
def archive_mandate(mandate_id: int, db: Session = Depends(get_db)) -> SearchMandateRead:
    service = SearchMandateService(db)
    mandate = service.get(mandate_id)
    if mandate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mandato no encontrado")
    return service.archive(mandate)


@router.get("/{mandate_id}/pipeline-count", response_model=dict[str, int])
def get_pipeline_count(mandate_id: int, db: Session = Depends(get_db)) -> dict[str, int]:
    service = SearchMandateService(db)
    mandate = service.get(mandate_id)
    if mandate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mandato no encontrado")
    return {"pipeline_count": service.pipeline_count(mandate_id)}
