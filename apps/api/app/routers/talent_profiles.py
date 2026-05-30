"""Rutas de la Bóveda de Talento (Talent Vault).

Sin auth en MVP (igual que el resto). Rutas bajo /api/talentos.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.talent_profile import (
    DuplicateDetectPayload,
    DuplicateDetectResponse,
    NoteCreatePayload,
    NoteUpdatePayload,
    TagAssignPayload,
    TalentDocumentRead,
    TalentEvaluationRead,
    TalentNoteRead,
    TalentProcessHistoryRead,
    TalentProfileCreate,
    TalentProfileListResponse,
    TalentProfileRead,
    TalentProfileUpdate,
    TalentTagRead,
)
from app.services.talent_profile_service import TalentProfileService

router = APIRouter(tags=["talent-vault"])


def _summary(service: TalentProfileService, p) -> dict:
    return {
        "id": p.id,
        "full_name": p.full_name,
        "current_position": p.current_position,
        "current_company": p.current_company,
        "inferred_seniority": p.inferred_seniority,
        "country": p.country,
        "city": p.city,
        "industries": list(p.industries or []),
        "skills": list(p.skills or []),
        "status": p.status,
        "availability_status": p.availability_status,
        "do_not_contact": p.do_not_contact,
        "last_score": service.latest_score(p.id),
        "last_evaluated_at": p.last_evaluated_at,
        "tags": service.list_tags_for(p.id),
        "evaluations_count": len(service.list_evaluations(p.id)),
        "updated_at": p.updated_at,
    }


def _full(service: TalentProfileService, p) -> dict:
    return {
        "id": p.id,
        "origin_candidate_id": p.origin_candidate_id,
        "full_name": p.full_name,
        "primary_email": p.primary_email,
        "primary_phone": p.primary_phone,
        "linkedin_url": p.linkedin_url,
        "current_position": p.current_position,
        "current_company": p.current_company,
        "country": p.country,
        "city": p.city,
        "general_location": p.general_location,
        "inferred_seniority": p.inferred_seniority,
        "summary": p.summary,
        "industries": list(p.industries or []),
        "skills": list(p.skills or []),
        "tools": list(p.tools or []),
        "languages": list(p.languages or []),
        "certifications": list(p.certifications or []),
        "education": list(p.education or []),
        "career_history": list(p.career_history or []),
        "achievements": list(p.achievements or []),
        "status": p.status,
        "availability_status": p.availability_status,
        "expected_compensation": p.expected_compensation,
        "do_not_contact": p.do_not_contact,
        "last_contacted_at": p.last_contacted_at,
        "last_evaluated_at": p.last_evaluated_at,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
        "tags": service.list_tags_for(p.id),
        "documents": service.list_documents(p.id),
        "evaluations": service.list_evaluations(p.id),
        "process_history": service.list_process_history(p.id),
        "notes": service.list_notes(p.id),
        "versions": service.list_versions(p.id),
    }


# --- Catálogo / utilidades (literales antes de /{talent_id}) ---------------


@router.get("/api/talentos/tags", response_model=list[TalentTagRead])
def list_tag_catalog(db: Session = Depends(get_db)) -> list:
    return TalentProfileService(db).list_tag_catalog()


@router.post(
    "/api/talentos/detectar-duplicados", response_model=DuplicateDetectResponse
)
def detect_duplicates(
    payload: DuplicateDetectPayload, db: Session = Depends(get_db)
) -> dict:
    matches = TalentProfileService(db).detect_duplicates(payload.model_dump())
    return {"has_potential_duplicates": len(matches) > 0, "matches": matches}


# --- CRUD perfil -----------------------------------------------------------


@router.get("/api/talentos", response_model=TalentProfileListResponse)
def list_talentos(
    db: Session = Depends(get_db),
    search: str | None = None,
    estado: str | None = Query(default=None),
    disponibilidad: str | None = Query(default=None),
    industria: str | None = Query(default=None),
    seniority: str | None = Query(default=None),
    skill: str | None = Query(default=None),
    min_score: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict:
    service = TalentProfileService(db)
    items, total = service.list_profiles(
        search=search,
        status=estado,
        availability=disponibilidad,
        industry=industria,
        seniority=seniority,
        skill=skill,
        min_score=min_score,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [_summary(service, p) for p in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "metrics": service.metrics(),
    }


@router.post("/api/talentos", response_model=TalentProfileRead, status_code=201)
def create_talento(payload: TalentProfileCreate, db: Session = Depends(get_db)) -> dict:
    service = TalentProfileService(db)
    profile = service.create(payload.model_dump())
    return _full(service, profile)


@router.get("/api/talentos/{talent_id}", response_model=TalentProfileRead)
def get_talento(talent_id: int, db: Session = Depends(get_db)) -> dict:
    service = TalentProfileService(db)
    profile = service.get(talent_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Talento no encontrado")
    return _full(service, profile)


@router.put("/api/talentos/{talent_id}", response_model=TalentProfileRead)
def update_talento(
    talent_id: int, payload: TalentProfileUpdate, db: Session = Depends(get_db)
) -> dict:
    service = TalentProfileService(db)
    data = payload.model_dump(exclude_unset=True)
    change_reason = data.pop("change_reason", None)
    profile = service.update(talent_id, data, change_reason=change_reason)
    if profile is None:
        raise HTTPException(status_code=404, detail="Talento no encontrado")
    return _full(service, profile)


@router.delete("/api/talentos/{talent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_talento(talent_id: int, db: Session = Depends(get_db)) -> None:
    if not TalentProfileService(db).soft_delete(talent_id):
        raise HTTPException(status_code=404, detail="Talento no encontrado")


# --- Sub-recursos de lectura -----------------------------------------------


@router.get(
    "/api/talentos/{talent_id}/documentos", response_model=list[TalentDocumentRead]
)
def list_documentos(talent_id: int, db: Session = Depends(get_db)) -> list:
    service = TalentProfileService(db)
    if service.get(talent_id) is None:
        raise HTTPException(status_code=404, detail="Talento no encontrado")
    return service.list_documents(talent_id)


@router.get(
    "/api/talentos/{talent_id}/evaluaciones", response_model=list[TalentEvaluationRead]
)
def list_evaluaciones(talent_id: int, db: Session = Depends(get_db)) -> list:
    service = TalentProfileService(db)
    if service.get(talent_id) is None:
        raise HTTPException(status_code=404, detail="Talento no encontrado")
    return service.list_evaluations(talent_id)


@router.get(
    "/api/talentos/{talent_id}/procesos",
    response_model=list[TalentProcessHistoryRead],
)
def list_procesos(talent_id: int, db: Session = Depends(get_db)) -> list:
    service = TalentProfileService(db)
    if service.get(talent_id) is None:
        raise HTTPException(status_code=404, detail="Talento no encontrado")
    return service.list_process_history(talent_id)


# --- Notas -----------------------------------------------------------------


@router.get("/api/talentos/{talent_id}/notas", response_model=list[TalentNoteRead])
def list_notas(talent_id: int, db: Session = Depends(get_db)) -> list:
    service = TalentProfileService(db)
    if service.get(talent_id) is None:
        raise HTTPException(status_code=404, detail="Talento no encontrado")
    return service.list_notes(talent_id)


@router.post(
    "/api/talentos/{talent_id}/notas", response_model=TalentNoteRead, status_code=201
)
def add_nota(
    talent_id: int, payload: NoteCreatePayload, db: Session = Depends(get_db)
) -> TalentNoteRead:
    note = TalentProfileService(db).add_note(talent_id, payload.model_dump())
    if note is None:
        raise HTTPException(status_code=404, detail="Talento no encontrado")
    return note


@router.put(
    "/api/talentos/{talent_id}/notas/{note_id}", response_model=TalentNoteRead
)
def update_nota(
    talent_id: int,
    note_id: int,
    payload: NoteUpdatePayload,
    db: Session = Depends(get_db),
) -> TalentNoteRead:
    note = TalentProfileService(db).update_note(
        talent_id, note_id, payload.model_dump(exclude_unset=True)
    )
    if note is None:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return note


@router.delete(
    "/api/talentos/{talent_id}/notas/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_nota(talent_id: int, note_id: int, db: Session = Depends(get_db)) -> None:
    if not TalentProfileService(db).delete_note(talent_id, note_id):
        raise HTTPException(status_code=404, detail="Nota no encontrada")


# --- Tags ------------------------------------------------------------------


@router.post(
    "/api/talentos/{talent_id}/tags", response_model=TalentProfileRead, status_code=201
)
def assign_tag(
    talent_id: int, payload: TagAssignPayload, db: Session = Depends(get_db)
) -> dict:
    service = TalentProfileService(db)
    tag = service.assign_tag(talent_id, payload.name, payload.category)
    if tag is None:
        raise HTTPException(status_code=404, detail="Talento no encontrado")
    return _full(service, service.get(talent_id))


@router.delete(
    "/api/talentos/{talent_id}/tags/{tag_id}", response_model=TalentProfileRead
)
def remove_tag(talent_id: int, tag_id: int, db: Session = Depends(get_db)) -> dict:
    service = TalentProfileService(db)
    if not service.remove_tag(talent_id, tag_id):
        raise HTTPException(status_code=404, detail="Tag no asignado a este talento")
    return _full(service, service.get(talent_id))
