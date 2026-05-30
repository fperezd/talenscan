"""Tests de la Bóveda de Talento (PR-TV-1/2): CRUD, versionamiento, notas,
tags, métricas y detección de duplicados."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def _create(client, **over):
    payload = {
        "full_name": "Ana Pérez",
        "primary_email": "ana@example.com",
        "current_position": "Gerenta Comercial",
        "current_company": "Falabella",
        "industries": ["Retail"],
        "skills": ["Ventas", "Liderazgo"],
        **over,
    }
    resp = client.post("/api/talentos", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_and_get(client):
    created = _create(client)
    assert created["full_name"] == "Ana Pérez"
    assert created["status"] == "active"
    assert created["availability_status"] == "unknown"
    # Creación genera versión 1
    got = client.get(f"/api/talentos/{created['id']}").json()
    assert got["id"] == created["id"]
    assert len(got["versions"]) == 1
    assert got["versions"][0]["version_number"] == 1


def test_get_unknown_404(client):
    assert client.get("/api/talentos/999999").status_code == 404


def test_list_with_metrics(client):
    _create(client, full_name="A", primary_email="a@x.com", availability_status="available")
    _create(client, full_name="B", primary_email="b@x.com")
    body = client.get("/api/talentos").json()
    assert body["total"] == 2
    assert len(body["items"]) == 2
    assert body["metrics"]["total"] == 2
    assert body["metrics"]["available"] >= 1


def test_list_search_filter(client):
    _create(client, full_name="Carlos Soto", primary_email="c@x.com", current_company="Cencosud")
    _create(client, full_name="Diana Rojas", primary_email="d@x.com", current_company="Falabella")
    body = client.get("/api/talentos", params={"search": "Cencosud"}).json()
    assert body["total"] == 1
    assert body["items"][0]["full_name"] == "Carlos Soto"


def test_update_creates_version(client):
    created = _create(client)
    resp = client.put(
        f"/api/talentos/{created['id']}",
        json={"current_company": "Cencosud", "change_reason": "Cambio de empresa"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["current_company"] == "Cencosud"
    # critical field changed → nueva versión (2 en total)
    assert len(body["versions"]) == 2


def test_update_noncritical_no_version(client):
    created = _create(client)
    resp = client.put(f"/api/talentos/{created['id']}", json={"city": "Santiago"})
    body = resp.json()
    assert body["city"] == "Santiago"
    assert len(body["versions"]) == 1  # no se versiona campo no crítico


def test_soft_delete(client):
    created = _create(client)
    assert client.delete(f"/api/talentos/{created['id']}").status_code == 204
    assert client.get(f"/api/talentos/{created['id']}").status_code == 404
    assert client.get("/api/talentos").json()["total"] == 0


def test_notes_crud(client):
    created = _create(client)
    tid = created["id"]
    note = client.post(
        f"/api/talentos/{tid}/notas",
        json={"note_type": "call", "note_text": "Llamada inicial"},
    ).json()
    assert note["note_type"] == "call"
    listed = client.get(f"/api/talentos/{tid}/notas").json()
    assert len(listed) == 1
    upd = client.put(
        f"/api/talentos/{tid}/notas/{note['id']}", json={"note_text": "Editada"}
    ).json()
    assert upd["note_text"] == "Editada"
    assert client.delete(f"/api/talentos/{tid}/notas/{note['id']}").status_code == 204
    assert client.get(f"/api/talentos/{tid}/notas").json() == []


def test_tags_assign_and_remove(client):
    created = _create(client)
    tid = created["id"]
    body = client.post(f"/api/talentos/{tid}/tags", json={"name": "Finalista"}).json()
    assert any(t["name"] == "Finalista" for t in body["tags"])
    tag_id = next(t["id"] for t in body["tags"] if t["name"] == "Finalista")
    # catálogo global
    catalog = client.get("/api/talentos/tags").json()
    assert any(t["name"] == "Finalista" for t in catalog)
    after = client.delete(f"/api/talentos/{tid}/tags/{tag_id}").json()
    assert all(t["name"] != "Finalista" for t in after["tags"])


def test_detect_duplicates(client):
    _create(client, full_name="Eva Lúz", primary_email="eva@corp.com", linkedin_url="https://linkedin.com/in/eva")
    # email exacto
    by_email = client.post(
        "/api/talentos/detectar-duplicados", json={"primary_email": "eva@corp.com"}
    ).json()
    assert by_email["has_potential_duplicates"] is True
    assert by_email["matches"][0]["match_reasons"] == ["email_exact"]
    assert by_email["matches"][0]["match_score"] >= 0.9
    # sin coincidencia
    none = client.post(
        "/api/talentos/detectar-duplicados", json={"primary_email": "otro@corp.com"}
    ).json()
    assert none["has_potential_duplicates"] is False
