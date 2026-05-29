from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.position_spec import PositionSpecRead, PositionSpecUpdate
from app.services.position_spec_service import PositionSpecService
from app.services.search_mandate_service import SearchMandateService

router = APIRouter(tags=["perfiles-objetivo"])


@router.post(
    "/api/mandatos/{mandate_id}/generar-perfil-objetivo",
    response_model=PositionSpecRead,
    status_code=status.HTTP_201_CREATED,
)
def generate_position_spec(mandate_id: int, db: Session = Depends(get_db)) -> PositionSpecRead:
    mandate_service = SearchMandateService(db)
    mandate = mandate_service.get(mandate_id)
    if mandate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mandato no encontrado")

    position_spec_service = PositionSpecService(db)
    created = position_spec_service.generate_from_mandate(mandate)
    mandate.status = "Perfil objetivo generado"
    db.add(mandate)
    db.commit()
    return created


@router.get("/api/mandatos/{mandate_id}/perfiles-objetivo", response_model=list[PositionSpecRead])
def list_position_specs_by_mandate(mandate_id: int, db: Session = Depends(get_db)) -> list[PositionSpecRead]:
    service = PositionSpecService(db)
    return service.list_by_mandate(mandate_id)


@router.get("/api/perfiles-objetivo/{position_spec_id}", response_model=PositionSpecRead)
def get_position_spec(position_spec_id: int, db: Session = Depends(get_db)) -> PositionSpecRead:
    service = PositionSpecService(db)
    item = service.get(position_spec_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil objetivo no encontrado")
    return item


@router.put("/api/perfiles-objetivo/{position_spec_id}", response_model=PositionSpecRead)
def update_position_spec(
    position_spec_id: int, payload: PositionSpecUpdate, db: Session = Depends(get_db)
) -> PositionSpecRead:
    service = PositionSpecService(db)
    item = service.get(position_spec_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil objetivo no encontrado")
    return service.update(item, payload)
