"""Tests del Decision Room (gate por código, sanitización, eventos, regeneración).

Crea fixtures mínimos directamente vía ORM para no depender de OpenAI ni
WeasyPrint. Lo crítico aquí es el comportamiento del gate y del flujo de
feedback/eventos, no el pipeline de IA.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.candidate import Candidate
from app.models.candidate_evaluation import CandidateEvaluation
from app.models.position_spec import PositionSpec
from app.models.search_mandate import SearchMandate


@pytest.fixture()
def session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield Session
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(session_factory):
    with TestClient(app) as test_client:
        yield test_client


def _seed_mandate_with_two_evaluations(SessionLocal) -> tuple[int, list[int]]:
    """Crea mandato + perfil objetivo + 2 candidatos + 2 evaluaciones."""
    with SessionLocal() as db:
        mandate = SearchMandate(
            client_name="ACME Corp",
            search_title="Búsqueda Head Comercial",
            target_role="Head Comercial",
            status="Activo",
        )
        db.add(mandate)
        db.flush()
        spec = PositionSpec(
            search_mandate_id=mandate.id,
            title="Head Comercial",
        )
        db.add(spec)
        db.flush()
        cand_a = Candidate(full_name="Ana Pérez", current_position="Gerenta", current_company="X")
        cand_b = Candidate(full_name="Bruno Díaz", current_position="Director", current_company="Y")
        db.add_all([cand_a, cand_b])
        db.flush()
        eval_a = CandidateEvaluation(
            candidate_id=cand_a.id,
            position_spec_id=spec.id,
            total_score=88,
            score_category="Muy alto calce",
            recommendation="Priorizar entrevista",
            executive_summary="…",
            evaluation_json={
                "ai_assessment": {
                    "talent_thesis": "Líder comercial con foco en SaaS",
                    "strengths_detailed": [
                        {"title": "Liderazgo", "detail": "10 años dirigiendo equipos"},
                    ],
                    "critical_gaps_detailed": [
                        {"requirement": "Inglés C1"},
                    ],
                }
            },
        )
        eval_b = CandidateEvaluation(
            candidate_id=cand_b.id,
            position_spec_id=spec.id,
            total_score=72,
            score_category="Buen calce",
            recommendation="Avanzar a entrevista",
            executive_summary="…",
            evaluation_json={"ai_assessment": {}},
        )
        db.add_all([eval_a, eval_b])
        db.commit()
        return mandate.id, [eval_a.id, eval_b.id]


def _create_room(client, mandate_id, eval_ids, **overrides):
    payload = {
        "title": "Decision Room ACME",
        "message_to_client": "Bienvenido",
        "evaluation_ids": eval_ids,
        **overrides,
    }
    response = client.post(f"/api/mandatos/{mandate_id}/shortlists", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# --- Creación + estados básicos --------------------------------------------


def test_create_room_starts_in_ready_to_share_when_has_candidates(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids)
    assert room["status"] == "ready_to_share"
    assert len(room["items"]) == 2
    assert room["access_code_required"] is False
    assert room["public_token"]
    assert len(room["public_token"]) >= 20  # token no secuencial


def test_public_view_without_gate_works_immediately(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids)
    response = client.get(f"/api/public/shortlists/{room['public_token']}")
    assert response.status_code == 200
    data = response.json()
    assert "candidates" in data
    assert len(data["candidates"]) == 2


# --- Access code -----------------------------------------------------------


def test_issue_access_code_returns_6_digits(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids)
    response = client.post(
        f"/api/shortlists/{room['id']}/access-code", json={"ttl_hours": 168}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"].isdigit() and len(body["code"]) == 6
    assert body["code_expires_at"]


def test_public_view_returns_gate_when_code_required(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(
        client,
        mandate_id,
        eval_ids,
        access_code_required=True,
        client_contact_email="cliente@acme.com",
    )
    issued = client.post(
        f"/api/shortlists/{room['id']}/access-code", json={"ttl_hours": 24}
    ).json()

    # Sin sesión → gate
    gate = client.get(f"/api/public/shortlists/{room['public_token']}").json()
    assert gate.get("requires_code") is True
    assert "candidates" not in gate
    # Hint enmascarado, no email completo
    assert gate.get("client_contact_email_hint", "").startswith("c***@")

    # Código incorrecto → 401, sin filtrar nada
    bad = client.post(
        f"/api/public/shortlists/{room['public_token']}/validate-code",
        json={"code": "000000"},
    )
    assert bad.status_code == 401

    # Código correcto → session token
    ok = client.post(
        f"/api/public/shortlists/{room['public_token']}/validate-code",
        json={"code": issued["code"]},
    )
    assert ok.status_code == 200
    session_token = ok.json()["session_token"]
    assert session_token

    # Con session token → vista completa
    view = client.get(
        f"/api/public/shortlists/{room['public_token']}",
        headers={"X-Decision-Room-Session": session_token},
    )
    assert view.status_code == 200
    assert "candidates" in view.json()
    assert len(view.json()["candidates"]) == 2


def test_validate_code_format_rejected_before_hitting_logic(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids, access_code_required=True)
    # No es 6 dígitos
    bad = client.post(
        f"/api/public/shortlists/{room['public_token']}/validate-code",
        json={"code": "abcd12"},
    )
    assert bad.status_code == 422


def test_regenerate_access_invalidates_previous(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids, access_code_required=True)
    first_token = room["public_token"]
    issued_first = client.post(
        f"/api/shortlists/{room['id']}/access-code", json={"ttl_hours": 24}
    ).json()

    regen = client.post(
        f"/api/shortlists/{room['id']}/regenerate-access", json={"ttl_hours": 24}
    )
    assert regen.status_code == 200
    new_token = regen.json()["public_token"]
    new_code = regen.json()["code"]
    assert new_token != first_token
    assert new_code != issued_first["code"]

    # Token viejo → 404
    old = client.get(f"/api/public/shortlists/{first_token}")
    assert old.status_code == 404

    # Código viejo en el token nuevo → 401
    bad = client.post(
        f"/api/public/shortlists/{new_token}/validate-code",
        json={"code": issued_first["code"]},
    )
    assert bad.status_code == 401

    # Código nuevo OK
    ok = client.post(
        f"/api/public/shortlists/{new_token}/validate-code",
        json={"code": new_code},
    )
    assert ok.status_code == 200


# --- Sanitización: no fugar campos ocultos ---------------------------------


def test_public_view_hides_score_when_toggle_off(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids, show_scores=False)
    view = client.get(f"/api/public/shortlists/{room['public_token']}").json()
    assert view["show_scores"] is False
    for c in view["candidates"]:
        assert c["score"] is None
        assert c["score_category"] is None


def test_public_view_hides_risks_when_toggle_off(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids, show_risks=False)
    view = client.get(f"/api/public/shortlists/{room['public_token']}").json()
    for c in view["candidates"]:
        assert c["risks_or_validations"] == []
        assert c["areas_to_validate"] == []


def test_public_view_hides_salary_unless_authorized_and_toggle_on(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids, show_salary=True)
    # Por default los items tienen salary_share_authorized=False → no se muestra
    item_id = room["items"][0]["id"]
    # Patcheamos el item con salario pero sin autorizar
    client.patch(
        f"/api/shortlists/{room['id']}/items/{item_id}",
        json={"salary_expectation": "$80M CLP", "salary_share_authorized": False},
    )
    view = client.get(f"/api/public/shortlists/{room['public_token']}").json()
    target = next(c for c in view["candidates"] if c["item_id"] == item_id)
    assert target["salary_expectation"] is None

    # Ahora autorizamos
    client.patch(
        f"/api/shortlists/{room['id']}/items/{item_id}",
        json={"salary_share_authorized": True},
    )
    view = client.get(f"/api/public/shortlists/{room['public_token']}").json()
    target = next(c for c in view["candidates"] if c["item_id"] == item_id)
    assert target["salary_expectation"] == "$80M CLP"


def test_invalid_token_returns_404_with_no_data(client):
    response = client.get("/api/public/shortlists/no-existe-12345")
    assert response.status_code == 404
    body = response.json()
    # Solo detail, ningún otro campo
    assert set(body.keys()) == {"detail"}


# --- Overrides + reorder + pin ---------------------------------------------


def test_update_item_overrides_persists_consultant_fields(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids)
    item_id = room["items"][0]["id"]
    response = client.patch(
        f"/api/shortlists/{room['id']}/items/{item_id}",
        json={
            "consultant_summary": "Resumen ejecutivo redactado por el consultor",
            "why_fits": ["10 años en SaaS", "Lideró equipos de 30+"],
            "risks_or_validations": ["Validar inglés C1"],
            "recommendation": "highly_recommended",
            "evidence_level": "high",
            "availability": "Disponible en 30 días",
        },
    )
    assert response.status_code == 200
    items = {it["id"]: it for it in response.json()["items"]}
    item = items[item_id]
    assert item["consultant_summary"].startswith("Resumen ejecutivo")
    assert item["why_fits"] == ["10 años en SaaS", "Lideró equipos de 30+"]
    assert item["recommendation"] == "highly_recommended"
    assert item["availability"] == "Disponible en 30 días"


def test_pin_moves_item_to_top(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids)
    # eval_a (score 88) viene primero; pin al segundo (Bruno).
    second_id = room["items"][1]["id"]
    client.post(
        f"/api/shortlists/{room['id']}/items/{second_id}/pin",
        json={"pinned": True},
    )
    view = client.get(f"/api/public/shortlists/{room['public_token']}").json()
    assert view["candidates"][0]["item_id"] == second_id


def test_reorder_persists_new_order(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids)
    first_id, second_id = room["items"][0]["id"], room["items"][1]["id"]
    response = client.patch(
        f"/api/shortlists/{room['id']}/items/reorder",
        json={"ordered_item_ids": [second_id, first_id]},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["id"] == second_id
    assert items[1]["id"] == first_id


# --- Feedback con estados nuevos -------------------------------------------


@pytest.mark.parametrize(
    "status_value",
    [
        "interested",
        "want_interview",
        "not_interested",
        "favorite",
        "interview_requested",
        "more_info_requested",
        "keep_in_review",
        "rejected",
    ],
)
def test_feedback_accepts_all_status_values(client, session_factory, status_value):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids)
    item_id = room["items"][0]["id"]
    response = client.post(
        f"/api/public/shortlists/{room['public_token']}/items/{item_id}/feedback",
        json={"client_status": status_value, "client_comment": "OK"},
    )
    assert response.status_code == 200
    assert response.json()["client_status"] == status_value


def test_feedback_rejects_invalid_status(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids)
    item_id = room["items"][0]["id"]
    response = client.post(
        f"/api/public/shortlists/{room['public_token']}/items/{item_id}/feedback",
        json={"client_status": "totalmente-invalido"},
    )
    # Pydantic Literal rechaza con 422
    assert response.status_code == 422


def test_feedback_blocked_when_room_requires_code_and_no_session(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids, access_code_required=True)
    client.post(f"/api/shortlists/{room['id']}/access-code", json={"ttl_hours": 24})
    item_id = room["items"][0]["id"]
    response = client.post(
        f"/api/public/shortlists/{room['public_token']}/items/{item_id}/feedback",
        json={"client_status": "favorite"},
    )
    assert response.status_code == 401


# --- Eventos / timeline ----------------------------------------------------


def test_events_timeline_records_lifecycle(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids)
    # Reorder
    first_id, second_id = room["items"][0]["id"], room["items"][1]["id"]
    client.patch(
        f"/api/shortlists/{room['id']}/items/reorder",
        json={"ordered_item_ids": [second_id, first_id]},
    )
    # Feedback público
    client.post(
        f"/api/public/shortlists/{room['public_token']}/items/{first_id}/feedback",
        json={"client_status": "interview_requested"},
    )
    events = client.get(f"/api/shortlists/{room['id']}/events").json()
    types = {e["event_type"] for e in events}
    assert "room_created" in types
    assert "candidate_reordered" in types
    assert "client_requested_interview" in types


# --- Revoke / close --------------------------------------------------------


def test_revoke_blocks_public_access(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids)
    client.post(f"/api/shortlists/{room['id']}/revoke")
    response = client.get(f"/api/public/shortlists/{room['public_token']}")
    assert response.status_code == 410


def test_close_room_marks_closed_status(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids)
    response = client.post(f"/api/shortlists/{room['id']}/close")
    assert response.status_code == 200
    assert response.json()["status"] == "closed"
    assert response.json()["closed_at"]


# --- Expiración ------------------------------------------------------------


def test_public_access_410_when_link_expired(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    room = _create_room(client, mandate_id, eval_ids, expires_at=past)
    response = client.get(f"/api/public/shortlists/{room['public_token']}")
    assert response.status_code == 410


def test_add_item_to_existing_room(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    # Crea room solo con primera evaluación
    room = _create_room(client, mandate_id, [eval_ids[0]])
    assert len(room["items"]) == 1
    # Agrega la segunda
    response = client.post(
        f"/api/shortlists/{room['id']}/items",
        json={"evaluation_id": eval_ids[1]},
    )
    assert response.status_code == 201
    body = response.json()
    assert len(body["items"]) == 2
    # Idempotente: agregar la misma de nuevo no duplica
    again = client.post(
        f"/api/shortlists/{room['id']}/items",
        json={"evaluation_id": eval_ids[1]},
    )
    assert again.status_code == 201
    assert len(again.json()["items"]) == 2


def test_remove_item_from_room(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids)
    item_id = room["items"][0]["id"]
    response = client.delete(f"/api/shortlists/{room['id']}/items/{item_id}")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert all(i["id"] != item_id for i in items)


def test_public_pdf_403_when_not_authorized(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids, allow_report_download=False)
    item_id = room["items"][0]["id"]
    response = client.get(
        f"/api/public/shortlists/{room['public_token']}/items/{item_id}/reporte/pdf"
    )
    assert response.status_code == 403


def test_public_pdf_401_when_code_required_and_no_session(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(
        client,
        mandate_id,
        eval_ids,
        allow_report_download=True,
        access_code_required=True,
    )
    item_id = room["items"][0]["id"]
    response = client.get(
        f"/api/public/shortlists/{room['public_token']}/items/{item_id}/reporte/pdf"
    )
    assert response.status_code == 401


def test_invitation_marker_updates_status(client, session_factory):
    mandate_id, eval_ids = _seed_mandate_with_two_evaluations(session_factory)
    room = _create_room(client, mandate_id, eval_ids)
    response = client.post(f"/api/shortlists/{room['id']}/invitation-sent")
    assert response.status_code == 200
    assert response.json()["status"] == "invitation_sent"
    assert response.json()["last_invitation_sent_at"]
