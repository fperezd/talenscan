from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.position_spec_generator import generate_position_spec_payload
from app.models.position_spec import PositionSpec
from app.models.search_mandate import SearchMandate
from app.schemas.position_spec import PositionSpecCreate, PositionSpecUpdate


class PositionSpecService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: PositionSpecCreate) -> PositionSpec:
        item = PositionSpec(**payload.model_dump())
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def generate_from_mandate(self, mandate: SearchMandate) -> PositionSpec:
        payload = PositionSpecCreate(search_mandate_id=mandate.id, **generate_position_spec_payload(mandate))
        return self.create(payload)

    def list_by_mandate(self, mandate_id: int) -> list[PositionSpec]:
        query = (
            select(PositionSpec)
            .where(PositionSpec.search_mandate_id == mandate_id)
            .order_by(PositionSpec.created_at.desc())
        )
        return list(self.db.scalars(query).all())

    def get(self, position_spec_id: int) -> PositionSpec | None:
        return self.db.get(PositionSpec, position_spec_id)

    def update(self, item: PositionSpec, payload: PositionSpecUpdate) -> PositionSpec:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item
