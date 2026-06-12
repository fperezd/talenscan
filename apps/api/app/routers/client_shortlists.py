"""Rutas para Decision Room (alias técnico: client_shortlists).

Admin (futuro: requerirá staff TalentScan; hoy sin auth como el resto del API):
    POST   /api/mandatos/{mandate_id}/shortlists
    GET    /api/mandatos/{mandate_id}/shortlists
    GET    /api/shortlists/{shortlist_id}
    PATCH  /api/shortlists/{shortlist_id}/config
    PATCH  /api/shortlists/{shortlist_id}/items/{item_id}
    PATCH  /api/shortlists/{shortlist_id}/items/reorder
    POST   /api/shortlists/{shortlist_id}/items/{item_id}/pin
    POST   /api/shortlists/{shortlist_id}/access-code
    POST   /api/shortlists/{shortlist_id}/regenerate-access
    POST   /api/shortlists/{shortlist_id}/invitation-sent
    POST   /api/shortlists/{shortlist_id}/close
    POST   /api/shortlists/{shortlist_id}/revoke
    DELETE /api/shortlists/{shortlist_id}
    GET    /api/shortlists/{shortlist_id}/events

Público (sin auth, mediante token):
    GET    /api/public/shortlists/{token}          — gate o vista, según config
    POST   /api/public/shortlists/{token}/validate-code
    POST   /api/public/shortlists/{token}/items/{item_id}/feedback
"""

from __future__ import annotations

import re
import unicodedata
from io import BytesIO

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.candidate import Candidate
from app.models.candidate_evaluation import CandidateEvaluation
from app.models.client_shortlist import ClientShortlistItem
from app.services.candidate_evaluation_service import CandidateEvaluationService
from app.services.report_service import ReportService
from app.schemas.client_shortlist import (
    AccessCodeIssuePayload,
    AccessCodeIssueResponse,
    AccessCodeValidatePayload,
    AccessCodeValidateResponse,
    ClientShortlistConfigUpdate,
    ClientShortlistCreate,
    ClientShortlistRead,
    DecisionRoomAddItemPayload,
    DecisionRoomCloseResponse,
    DecisionRoomEventRead,
    DecisionRoomItemOverrides,
    DecisionRoomPinPayload,
    DecisionRoomReorderPayload,
    PublicFeedbackPayload,
    PublicShortlistGateView,
    PublicShortlistView,
    RegenerateAccessResponse,
)
from app.services.client_shortlist_service import (
    ClientShortlistService,
    verify_client_session,
)

router = APIRouter(tags=["decision-room"])


def _serialize(service: ClientShortlistService, shortlist) -> dict:
    items = service.items_for(shortlist.id)
    db = service.db
    # Pre-cargo candidatos y evaluaciones referenciados para evitar N+1.
    candidate_ids = {item.candidate_id for item in items}
    evaluation_ids = {item.evaluation_id for item in items if item.evaluation_id}
    candidates_by_id = {
        c.id: c
        for c in (db.get(Candidate, cid) for cid in candidate_ids)
        if c is not None
    }
    evaluations_by_id = {
        e.id: e
        for e in (db.get(CandidateEvaluation, eid) for eid in evaluation_ids)
        if e is not None
    }
    return {
        "id": shortlist.id,
        "mandate_id": shortlist.mandate_id,
        "public_token": shortlist.public_token,
        "title": shortlist.title,
        "message_to_client": shortlist.message_to_client,
        "intro_message": shortlist.intro_message,
        "show_scores": shortlist.show_scores,
        "show_availability": shortlist.show_availability,
        "show_salary": shortlist.show_salary,
        "show_risks": shortlist.show_risks,
        "show_comparison": shortlist.show_comparison,
        "allow_comments": shortlist.allow_comments,
        "allow_rating": shortlist.allow_rating,
        "allow_report_download": shortlist.allow_report_download,
        "access_code_required": shortlist.access_code_required,
        "access_code_expires_at": shortlist.access_code_expires_at,
        "expires_at": shortlist.expires_at,
        "revoked": shortlist.revoked,
        "status": shortlist.status,
        "client_contact_name": shortlist.client_contact_name,
        "client_contact_email": shortlist.client_contact_email,
        "client_contact_company": shortlist.client_contact_company,
        "last_invitation_sent_at": shortlist.last_invitation_sent_at,
        "viewed_at": shortlist.viewed_at,
        "viewed_count": shortlist.viewed_count,
        "closed_at": shortlist.closed_at,
        "created_at": shortlist.created_at,
        "updated_at": shortlist.updated_at,
        "items": [
            {
                "id": item.id,
                "shortlist_id": item.shortlist_id,
                "candidate_id": item.candidate_id,
                "evaluation_id": item.evaluation_id,
                "order_index": item.order_index,
                "is_pinned": item.is_pinned,
                "recommendation": item.recommendation,
                "consultant_summary": item.consultant_summary,
                "why_fits": list(item.why_fits or []),
                "risks_or_validations": list(item.risks_or_validations or []),
                "evidence_level": item.evidence_level,
                "availability": item.availability,
                "salary_expectation": item.salary_expectation,
                "salary_share_authorized": item.salary_share_authorized,
                "rating": item.rating,
                "client_status": item.client_status,
                "client_comment": item.client_comment,
                "status_updated_at": item.status_updated_at,
                "created_at": item.created_at,
                "candidate_name": (
                    candidates_by_id[item.candidate_id].full_name
                    if item.candidate_id in candidates_by_id
                    else None
                ),
                "candidate_current_position": (
                    candidates_by_id[item.candidate_id].current_position
                    if item.candidate_id in candidates_by_id
                    else None
                ),
                "candidate_current_company": (
                    candidates_by_id[item.candidate_id].current_company
                    if item.candidate_id in candidates_by_id
                    else None
                ),
                "candidate_linkedin_url": (
                    candidates_by_id[item.candidate_id].linkedin_url
                    if item.candidate_id in candidates_by_id
                    else None
                ),
                "evaluation_score": (
                    evaluations_by_id[item.evaluation_id].total_score
                    if item.evaluation_id in evaluations_by_id
                    else None
                ),
                "evaluation_score_category": (
                    evaluations_by_id[item.evaluation_id].score_category
                    if item.evaluation_id in evaluations_by_id
                    else None
                ),
            }
            for item in items
        ],
    }


# --- Admin: CRUD del Decision Room -----------------------------------------


@router.post(
    "/api/mandatos/{mandate_id}/shortlists",
    response_model=ClientShortlistRead,
    status_code=status.HTTP_201_CREATED,
)
def create_shortlist(
    mandate_id: int,
    payload: ClientShortlistCreate,
    db: Session = Depends(get_db),
) -> dict:
    service = ClientShortlistService(db)
    try:
        shortlist = service.create(
            mandate_id=mandate_id,
            title=payload.title,
            message_to_client=payload.message_to_client,
            intro_message=payload.intro_message,
            show_scores=payload.show_scores,
            show_availability=payload.show_availability,
            show_salary=payload.show_salary,
            show_risks=payload.show_risks,
            show_comparison=payload.show_comparison,
            allow_comments=payload.allow_comments,
            allow_rating=payload.allow_rating,
            allow_report_download=payload.allow_report_download,
            access_code_required=payload.access_code_required,
            evaluation_ids=payload.evaluation_ids,
            expires_at=payload.expires_at,
            client_contact_name=payload.client_contact_name,
            client_contact_email=payload.client_contact_email,
            client_contact_company=payload.client_contact_company,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return _serialize(service, shortlist)


@router.get(
    "/api/mandatos/{mandate_id}/shortlists",
    response_model=list[ClientShortlistRead],
)
def list_shortlists_by_mandate(mandate_id: int, db: Session = Depends(get_db)) -> list[dict]:
    service = ClientShortlistService(db)
    return [_serialize(service, sl) for sl in service.list_by_mandate(mandate_id)]


@router.get(
    "/api/shortlists",
    response_model=list[ClientShortlistRead],
)
def list_all_shortlists(db: Session = Depends(get_db)) -> list[dict]:
    """Listado global de Decision Rooms, usado por el dashboard."""
    service = ClientShortlistService(db)
    return [_serialize(service, sl) for sl in service.list_all()]


@router.get("/api/shortlists/{shortlist_id}", response_model=ClientShortlistRead)
def get_shortlist(shortlist_id: int, db: Session = Depends(get_db)) -> dict:
    service = ClientShortlistService(db)
    shortlist = service.get(shortlist_id)
    if shortlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision Room no encontrado")
    return _serialize(service, shortlist)


@router.patch("/api/shortlists/{shortlist_id}/config", response_model=ClientShortlistRead)
def update_config(
    shortlist_id: int,
    payload: ClientShortlistConfigUpdate,
    db: Session = Depends(get_db),
) -> dict:
    service = ClientShortlistService(db)
    shortlist = service.update_config(shortlist_id, payload.model_dump(exclude_unset=True))
    if shortlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision Room no encontrado")
    return _serialize(service, shortlist)


@router.post(
    "/api/shortlists/{shortlist_id}/items",
    response_model=ClientShortlistRead,
    status_code=status.HTTP_201_CREATED,
)
def add_item_to_room(
    shortlist_id: int,
    payload: DecisionRoomAddItemPayload,
    db: Session = Depends(get_db),
) -> dict:
    service = ClientShortlistService(db)
    try:
        item = service.add_item(shortlist_id, payload.evaluation_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Decision Room no encontrado"
        )
    shortlist = service.get(shortlist_id)
    return _serialize(service, shortlist)


@router.delete(
    "/api/shortlists/{shortlist_id}/items/{item_id}",
    response_model=ClientShortlistRead,
)
def remove_item_from_room(
    shortlist_id: int,
    item_id: int,
    db: Session = Depends(get_db),
) -> dict:
    service = ClientShortlistService(db)
    if not service.remove_item(shortlist_id, item_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item no encontrado en el Decision Room",
        )
    shortlist = service.get(shortlist_id)
    return _serialize(service, shortlist)


@router.patch("/api/shortlists/{shortlist_id}/items/reorder", response_model=ClientShortlistRead)
def reorder_items(
    shortlist_id: int,
    payload: DecisionRoomReorderPayload,
    db: Session = Depends(get_db),
) -> dict:
    service = ClientShortlistService(db)
    shortlist = service.get(shortlist_id)
    if shortlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision Room no encontrado")
    service.reorder_items(shortlist_id, payload.ordered_item_ids)
    shortlist = service.get(shortlist_id)
    return _serialize(service, shortlist)


@router.patch("/api/shortlists/{shortlist_id}/items/{item_id}", response_model=ClientShortlistRead)
def update_item_overrides(
    shortlist_id: int,
    item_id: int,
    payload: DecisionRoomItemOverrides,
    db: Session = Depends(get_db),
) -> dict:
    service = ClientShortlistService(db)
    item = service.update_item_overrides(
        shortlist_id, item_id, payload.model_dump(exclude_unset=True)
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item del Decision Room no encontrado",
        )
    shortlist = service.get(shortlist_id)
    return _serialize(service, shortlist)


@router.post("/api/shortlists/{shortlist_id}/items/{item_id}/pin", response_model=ClientShortlistRead)
def pin_item(
    shortlist_id: int,
    item_id: int,
    payload: DecisionRoomPinPayload,
    db: Session = Depends(get_db),
) -> dict:
    service = ClientShortlistService(db)
    item = service.pin_item(shortlist_id, item_id, payload.pinned)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item del Decision Room no encontrado",
        )
    shortlist = service.get(shortlist_id)
    return _serialize(service, shortlist)


# --- Admin: access code ----------------------------------------------------


@router.post(
    "/api/shortlists/{shortlist_id}/access-code",
    response_model=AccessCodeIssueResponse,
)
def issue_access_code(
    shortlist_id: int,
    payload: AccessCodeIssuePayload,
    db: Session = Depends(get_db),
) -> dict:
    service = ClientShortlistService(db)
    try:
        shortlist, code, code_exp = service.issue_access_code(
            shortlist_id, ttl_hours=payload.ttl_hours
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return {
        "code": code,
        "code_expires_at": code_exp,
        "access_expires_at": shortlist.expires_at,
    }


@router.post(
    "/api/shortlists/{shortlist_id}/regenerate-access",
    response_model=RegenerateAccessResponse,
)
def regenerate_access(
    shortlist_id: int,
    payload: AccessCodeIssuePayload,
    db: Session = Depends(get_db),
) -> dict:
    service = ClientShortlistService(db)
    try:
        _, public_token, code, code_exp = service.regenerate_access(
            shortlist_id, ttl_hours=payload.ttl_hours
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return {
        "public_token": public_token,
        "code": code,
        "code_expires_at": code_exp,
    }


@router.post(
    "/api/shortlists/{shortlist_id}/invitation-sent",
    response_model=ClientShortlistRead,
)
def mark_invitation_sent(shortlist_id: int, db: Session = Depends(get_db)) -> dict:
    service = ClientShortlistService(db)
    shortlist = service.mark_invitation_sent(shortlist_id)
    if shortlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision Room no encontrado")
    return _serialize(service, shortlist)


@router.post(
    "/api/shortlists/{shortlist_id}/close",
    response_model=DecisionRoomCloseResponse,
)
def close_room(shortlist_id: int, db: Session = Depends(get_db)) -> dict:
    service = ClientShortlistService(db)
    shortlist = service.close_room(shortlist_id)
    if shortlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision Room no encontrado")
    return {"id": shortlist.id, "status": shortlist.status, "closed_at": shortlist.closed_at}


@router.post("/api/shortlists/{shortlist_id}/revoke", response_model=ClientShortlistRead)
def revoke_shortlist(shortlist_id: int, db: Session = Depends(get_db)) -> dict:
    service = ClientShortlistService(db)
    shortlist = service.revoke(shortlist_id)
    if shortlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision Room no encontrado")
    return _serialize(service, shortlist)


@router.delete("/api/shortlists/{shortlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shortlist(shortlist_id: int, db: Session = Depends(get_db)) -> None:
    service = ClientShortlistService(db)
    if not service.delete(shortlist_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision Room no encontrado")


@router.get(
    "/api/shortlists/{shortlist_id}/events",
    response_model=list[DecisionRoomEventRead],
)
def list_events(shortlist_id: int, db: Session = Depends(get_db)) -> list[dict]:
    service = ClientShortlistService(db)
    shortlist = service.get(shortlist_id)
    if shortlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision Room no encontrado")
    return [
        {
            "id": event.id,
            "shortlist_id": event.shortlist_id,
            "item_id": event.item_id,
            "event_type": event.event_type,
            "event_label": event.event_label,
            "actor_type": event.actor_type,
            "actor_name": event.actor_name,
            "actor_email": event.actor_email,
            "event_metadata": dict(event.event_metadata or {}),
            "created_at": event.created_at,
        }
        for event in service.list_events(shortlist_id)
    ]


# --- Public endpoints (no auth) -------------------------------------------


def _ensure_link_active(service: ClientShortlistService, shortlist) -> None:
    link_status = service.link_status_or_none(shortlist)
    if link_status == "revoked":
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Este Decision Room fue revocado por TalentScan.",
        )
    if link_status == "expired":
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Este acceso expiró. Solicita un nuevo link a TalentScan.",
        )
    if link_status == "closed":
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Este Decision Room fue cerrado.",
        )


@router.get("/api/public/shortlists/{token}")
def get_public_shortlist(
    token: str,
    db: Session = Depends(get_db),
    x_decision_room_session: str | None = Header(default=None, alias="X-Decision-Room-Session"),
):
    service = ClientShortlistService(db)
    shortlist = service.get_by_token(token)
    if shortlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision Room no encontrado")
    _ensure_link_active(service, shortlist)

    # Si el room exige código y el cliente no trajo sesión válida → gate view.
    if shortlist.access_code_required and not verify_client_session(
        x_decision_room_session, shortlist.id
    ):
        return PublicShortlistGateView(**service.build_gate_view(shortlist))

    service.register_view(shortlist)
    return PublicShortlistView(**service.build_public_view(shortlist))


@router.post(
    "/api/public/shortlists/{token}/validate-code",
    response_model=AccessCodeValidateResponse,
)
def validate_code(
    token: str,
    payload: AccessCodeValidatePayload,
    db: Session = Depends(get_db),
) -> dict:
    service = ClientShortlistService(db)
    shortlist = service.get_by_token(token)
    if shortlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision Room no encontrado")
    _ensure_link_active(service, shortlist)

    result = service.validate_access_code(token, payload.code)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código incorrecto, expirado o ya consumido.",
        )
    session_token, session_exp = result
    return {"session_token": session_token, "session_expires_at": session_exp}


def _slug(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value or "")
    no_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    cleaned = re.sub(r"[^A-Za-z0-9\s-]", "", no_accents).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned or "Candidato"


@router.get("/api/public/shortlists/{token}/items/{item_id}/reporte/pdf")
def download_public_report(
    token: str,
    item_id: int,
    db: Session = Depends(get_db),
    x_decision_room_session: str | None = Header(default=None, alias="X-Decision-Room-Session"),
) -> StreamingResponse:
    """Devuelve el PDF del Scan 360 si el room lo autorizó.

    Reglas de seguridad:
    - Room debe estar activo (no revocado/cerrado/expirado).
    - Si access_code_required, exige sesión validada por header.
    - allow_report_download debe estar activo.
    - El item debe pertenecer al room y tener evaluación asociada.
    """
    service = ClientShortlistService(db)
    shortlist = service.get_by_token(token)
    if shortlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision Room no encontrado")
    _ensure_link_active(service, shortlist)

    if shortlist.access_code_required and not verify_client_session(
        x_decision_room_session, shortlist.id
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Debes validar el código antes de descargar el informe.",
        )
    if not shortlist.allow_report_download:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El consultor no autorizó la descarga del informe en este Decision Room.",
        )

    item = db.get(ClientShortlistItem, item_id)
    if item is None or item.shortlist_id != shortlist.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Candidato no encontrado en el Decision Room."
        )
    if item.evaluation_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Este candidato no tiene evaluación generada."
        )

    evaluation = CandidateEvaluationService(db).get(item.evaluation_id)
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluación no disponible.")

    candidate = db.get(Candidate, item.candidate_id)
    file_bytes = ReportService(db).generate_pdf(evaluation)
    file_name = f"Scan360_{_slug(candidate.full_name if candidate else f'Candidato_{item.candidate_id}')}.pdf"
    return StreamingResponse(
        BytesIO(file_bytes),
        media_type="application/pdf",
        headers={
            # inline → el browser lo renderiza en una pestaña en vez de descargar
            "Content-Disposition": f'inline; filename="{file_name}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.post("/api/public/shortlists/{token}/items/{item_id}/feedback")
def record_public_feedback(
    token: str,
    item_id: int,
    payload: PublicFeedbackPayload,
    db: Session = Depends(get_db),
    x_decision_room_session: str | None = Header(default=None, alias="X-Decision-Room-Session"),
) -> dict:
    service = ClientShortlistService(db)
    shortlist = service.get_by_token(token)
    if shortlist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision Room no encontrado.",
        )
    # Si el room exige código, exigir sesión validada antes de aceptar feedback.
    if shortlist.access_code_required and not verify_client_session(
        x_decision_room_session, shortlist.id
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Debes ingresar el código de validación antes de dejar feedback.",
        )
    try:
        item = service.record_feedback(
            token=token,
            item_id=item_id,
            client_status=payload.client_status,
            client_comment=payload.client_comment,
            rating=payload.rating,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision Room o candidato no encontrado, o el link expiró.",
        )
    return {
        "item_id": item.id,
        "client_status": item.client_status,
        "client_comment": item.client_comment,
        "rating": item.rating,
        "status_updated_at": item.status_updated_at,
    }
