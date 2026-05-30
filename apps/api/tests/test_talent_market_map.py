"""Tests del Talent Market Map (entregable F1-F3).

Cubre:
- Motores deterministas puros: gap_detector + recommendation_engine.
- Fallback determinista del generador IA (sin red).
- Flujo completo de la API: get-or-create, generate (con generador mockeado),
  CRUD de segments/companies/equivalent-roles, recompute de brechas,
  regeneración + decisión de recomendaciones, asignación de candidatos,
  cobertura derivada, export de resumen y archivado.

Fixtures mínimos vía ORM, igual que test_decision_room, para no depender de
OpenAI ni WeasyPrint. La generación IA se mockea en el namespace del servicio.
"""

from __future__ import annotations

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
from app.models.candidate_pipeline_item import CandidatePipelineItem
from app.models.position_spec import PositionSpec
from app.models.search_mandate import SearchMandate


# --- Fixtures ---------------------------------------------------------------


@pytest.fixture()
def session_factory():
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
    try:
        yield SessionLocal
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(session_factory):
    with TestClient(app) as test_client:
        yield test_client


# --- Helpers de seed --------------------------------------------------------


def _seed_mandate_with_spec(
    SessionLocal,
    *,
    target_industries=None,
    target_companies=None,
    equivalent_roles=None,
) -> tuple[int, int]:
    """Crea un mandato + perfil objetivo con datos para el fallback. Devuelve (mandate_id, spec_id)."""
    with SessionLocal() as db:
        mandate = SearchMandate(
            client_name="ACME Corp",
            search_title="Búsqueda Gerente Comercial",
            target_role="Gerente Comercial",
            industry="Retail",
            country="Chile",
            seniority_level="Gerencia",
            status="Activo",
            target_companies=target_companies or ["Falabella", "Cencosud"],
            target_industries=target_industries or ["Retail", "Consumo masivo"],
            equivalent_roles=equivalent_roles or ["Head Comercial", "Director de Ventas"],
        )
        db.add(mandate)
        db.flush()
        spec = PositionSpec(
            search_mandate_id=mandate.id,
            title="Gerente Comercial",
            target_industries=["Retail", "Consumo masivo", "E-commerce"],
            target_company_types=["Retailer grande", "Marketplace"],
            equivalent_roles=["Head Comercial", "Director Comercial"],
        )
        db.add(spec)
        db.flush()
        ids = (mandate.id, spec.id)
        db.commit()
        return ids


def _add_candidate_with_eval(
    SessionLocal,
    mandate_id: int,
    spec_id: int,
    *,
    name: str,
    company: str,
    score: int,
    critical_gaps: list[dict] | None = None,
    stage: str = "evaluated",
    discard_reason: str = "",
) -> tuple[int, int]:
    """Crea candidato + evaluación + pipeline item. Devuelve (candidate_id, evaluation_id)."""
    with SessionLocal() as db:
        cand = Candidate(
            full_name=name,
            current_position="Gerente",
            current_company=company,
        )
        db.add(cand)
        db.flush()
        ev = CandidateEvaluation(
            candidate_id=cand.id,
            position_spec_id=spec_id,
            total_score=score,
            critical_gaps=critical_gaps or [],
        )
        db.add(ev)
        db.flush()
        item = CandidatePipelineItem(
            mandate_id=mandate_id,
            candidate_id=cand.id,
            evaluation_id=ev.id,
            stage=stage,
            discard_reason=discard_reason,
        )
        db.add(item)
        db.flush()
        ids = (cand.id, ev.id)
        db.commit()
        return ids


def _fake_payload() -> dict:
    """Payload determinista que reemplaza la salida del generador IA."""
    return {
        "executive_summary": "Resumen ejecutivo de prueba para el mapa de mercado.",
        "market_assessment": "moderate",
        "segments": [
            {
                "name": "Retail directo",
                "segment_type": "primary",
                "description": "Competidores directos en retail.",
                "priority": "high",
                "rationale": "Sector del cargo.",
            },
            {
                "name": "Consumo masivo",
                "segment_type": "adjacent",
                "description": "Perfiles transferibles.",
                "priority": "medium",
                "rationale": "Adyacente.",
            },
        ],
        "companies": [
            {
                "name": "Falabella",
                "industry": "Retail",
                "segment_name": "Retail directo",
                "priority": "high",
                "rationale": "Líder del sector.",
            },
            {
                "name": "Nestlé",
                "industry": "Consumo masivo",
                "segment_name": "Consumo masivo",
                "priority": "medium",
                "rationale": "Adyacente relevante.",
            },
        ],
        "equivalent_roles": [
            {
                "title": "Head Comercial",
                "seniority": "Gerencia",
                "closeness": "high",
                "priority": "high",
                "industries": ["Retail"],
                "rationale": "Mismo scope.",
            }
        ],
        "_meta": {
            "generated_by_model": "gpt-4o-mini",
            "prompt_version": "talent-market-map-v1",
        },
    }


# ===========================================================================
# Unit: gap_detector
# ===========================================================================


def test_gap_detector_empty_returns_empty():
    from app.scoring.gap_detector import detect_gaps

    assert detect_gaps([]) == []


def test_gap_detector_groups_and_thresholds():
    """Con >=3 evals, sólo brechas con frequency>=2; agrupa ignorando acentos."""
    from app.scoring.gap_detector import detect_gaps

    def ev(gaps):
        e = CandidateEvaluation(candidate_id=1, position_spec_id=1, total_score=50)
        e.critical_gaps = gaps
        return e

    evals = [
        ev([{"requirement": "Inglés avanzado", "reason": "No certifica", "impact": "high"}]),
        ev([{"requirement": "ingles avanzado", "reason": "Nivel básico", "impact": "high"}]),
        ev([{"requirement": "Disponibilidad viaje", "reason": "No puede", "impact": "low"}]),
    ]
    gaps = detect_gaps(evals)

    # "Inglés avanzado" / "ingles avanzado" se agrupan → frequency 2 (supera umbral)
    titles = {g["title"] for g in gaps}
    assert any("ngl" in t.lower() for t in titles)
    english = next(g for g in gaps if "ngl" in g["title"].lower())
    assert english["frequency"] == 2
    assert english["total_evaluated"] == 3
    assert english["impact"] == "high"
    # "Disponibilidad viaje" sólo aparece 1 vez → excluida (umbral 2 con total>=3)
    assert not any("disponibilidad" in t.lower() for t in titles)
    # Recomendación específica para inglés
    assert "inglés" in english["recommendation"].lower() or "ingles" in english["recommendation"].lower()


def test_gap_detector_low_total_accepts_frequency_one():
    """Con <3 evals, una brecha que aparece 1 vez igual se muestra."""
    from app.scoring.gap_detector import detect_gaps

    e = CandidateEvaluation(candidate_id=1, position_spec_id=1, total_score=40)
    e.critical_gaps = [{"requirement": "Experiencia en sector", "reason": "Otra industria", "impact": "medium"}]
    gaps = detect_gaps([e])
    assert len(gaps) == 1
    assert gaps[0]["frequency"] == 1
    assert gaps[0]["total_evaluated"] == 1


# ===========================================================================
# Unit: recommendation_engine
# ===========================================================================


def test_recommendation_engine_pipeline_without_evaluations():
    """R6: hay pipeline pero ninguna evaluación → sugiere correr Evaluación 360."""
    from app.scoring.recommendation_engine import generate_rule_recommendations

    items = [
        CandidatePipelineItem(mandate_id=1, candidate_id=1, evaluation_id=None, stage="received"),
        CandidatePipelineItem(mandate_id=1, candidate_id=2, evaluation_id=None, stage="received"),
    ]
    recs = generate_rule_recommendations(
        coverage_pct=0,
        target_companies=[],
        pipeline_items=items,
        evaluations_map={},
        gaps_data=[],
        shortlisted_count=0,
    )
    titles = [r["title"] for r in recs]
    assert any("Evaluaciones 360" in t for t in titles)
    assert all(r["generated_by"] == "rules" for r in recs)


def test_recommendation_engine_low_score_and_critical_gap():
    """R3 (score bajo) + R4 (brecha excluyente >=50%)."""
    from app.scoring.recommendation_engine import generate_rule_recommendations

    ev1 = CandidateEvaluation(candidate_id=1, position_spec_id=1, total_score=40)
    ev2 = CandidateEvaluation(candidate_id=2, position_spec_id=1, total_score=45)
    evals_map = {10: ev1, 11: ev2}
    items = [
        CandidatePipelineItem(mandate_id=1, candidate_id=1, evaluation_id=10, stage="evaluated"),
        CandidatePipelineItem(mandate_id=1, candidate_id=2, evaluation_id=11, stage="evaluated"),
    ]
    gaps = [{"title": "Inglés avanzado", "frequency": 2, "total_evaluated": 2, "impact": "high", "recommendation": "x"}]
    recs = generate_rule_recommendations(
        coverage_pct=40,
        target_companies=[],
        pipeline_items=items,
        evaluations_map=evals_map,
        gaps_data=gaps,
        shortlisted_count=0,
    )
    titles = " | ".join(r["title"] for r in recs)
    assert "calibración del perfil" in titles  # R3
    assert "relajar requisito" in titles.lower()  # R4


# ===========================================================================
# Unit: generador IA — fallback determinista (sin red)
# ===========================================================================


def test_generator_fallback_when_llm_unavailable(session_factory, monkeypatch):
    """Si generate_structured_json devuelve None, usa fallback desde el spec."""
    import app.ai.talent_market_map_generator as gen

    monkeypatch.setattr(gen, "generate_structured_json", lambda **kwargs: None)

    mandate_id, spec_id = _seed_mandate_with_spec(session_factory)
    with session_factory() as db:
        mandate = db.get(SearchMandate, mandate_id)
        spec = db.get(PositionSpec, spec_id)
        payload = gen.generate_talent_market_map(mandate, spec)

    assert payload["_meta"]["generated_by_model"] == "rules-fallback"
    assert payload["segments"], "el fallback siempre produce al menos un segmento"
    company_names = {c["name"] for c in payload["companies"]}
    assert "Falabella" in company_names  # viene del mandate.target_companies


# ===========================================================================
# API: get-or-create + 404
# ===========================================================================


def test_get_or_create_map(client, session_factory):
    mandate_id, spec_id = _seed_mandate_with_spec(session_factory)
    resp = client.get(f"/api/mandatos/{mandate_id}/talent-market-map")
    assert resp.status_code == 200
    body = resp.json()
    assert body["search_mandate_id"] == mandate_id
    assert body["position_spec_id"] == spec_id  # linkea el spec más reciente
    assert body["status"] == "draft"
    assert body["segments"] == []
    assert body["coverage"]["coverage_pct"] == 0

    # Idempotente: segunda llamada devuelve el mismo mapa
    resp2 = client.get(f"/api/mandatos/{mandate_id}/talent-market-map")
    assert resp2.json()["id"] == body["id"]


def test_get_or_create_map_unknown_mandate_404(client, session_factory):
    resp = client.get("/api/mandatos/999999/talent-market-map")
    assert resp.status_code == 404


# ===========================================================================
# API: generate (generador mockeado) + recompute automático
# ===========================================================================


def test_generate_persists_entities(client, session_factory, monkeypatch):
    import app.services.talent_market_map_service as svc

    monkeypatch.setattr(svc, "generate_talent_market_map", lambda mandate, spec: _fake_payload())

    mandate_id, spec_id = _seed_mandate_with_spec(session_factory)
    resp = client.post(f"/api/mandatos/{mandate_id}/talent-market-map/generate")
    assert resp.status_code == 200
    body = resp.json()

    assert body["status"] == "generated"
    assert body["executive_summary"] == "Resumen ejecutivo de prueba para el mapa de mercado."
    assert body["generated_by_model"] == "gpt-4o-mini"
    assert {s["name"] for s in body["segments"]} == {"Retail directo", "Consumo masivo"}
    assert all(s["ai_suggested"] for s in body["segments"])
    # La empresa "Falabella" debe quedar ligada al segmento "Retail directo"
    falabella = next(c for c in body["companies"] if c["name"] == "Falabella")
    retail_seg = next(s for s in body["segments"] if s["name"] == "Retail directo")
    assert falabella["segment_id"] == retail_seg["id"]
    assert len(body["equivalent_roles"]) == 1


def test_generate_preserves_manual_segments(client, session_factory, monkeypatch):
    """Regenerar con IA no pisa entidades creadas manualmente (ai_suggested=False)."""
    import app.services.talent_market_map_service as svc

    monkeypatch.setattr(svc, "generate_talent_market_map", lambda mandate, spec: _fake_payload())

    mandate_id, _ = _seed_mandate_with_spec(session_factory)
    map_resp = client.get(f"/api/mandatos/{mandate_id}/talent-market-map").json()
    map_id = map_resp["id"]

    # Segmento manual
    client.post(
        f"/api/talent-market-maps/{map_id}/segments",
        json={"name": "Segmento manual", "segment_type": "exploratory"},
    )
    # Generar con IA
    gen = client.post(f"/api/mandatos/{mandate_id}/talent-market-map/generate").json()
    names = {s["name"] for s in gen["segments"]}
    assert "Segmento manual" in names  # preservado
    assert "Retail directo" in names  # sumado por IA


# ===========================================================================
# API: CRUD segments / companies / roles
# ===========================================================================


def test_segment_crud_and_reorder(client, session_factory):
    mandate_id, _ = _seed_mandate_with_spec(session_factory)
    map_id = client.get(f"/api/mandatos/{mandate_id}/talent-market-map").json()["id"]

    a = client.post(
        f"/api/talent-market-maps/{map_id}/segments",
        json={"name": "Seg A", "segment_type": "primary"},
    ).json()
    seg_a = next(s for s in a["segments"] if s["name"] == "Seg A")
    assert seg_a["ai_suggested"] is False

    b = client.post(
        f"/api/talent-market-maps/{map_id}/segments",
        json={"name": "Seg B", "segment_type": "adjacent"},
    ).json()
    seg_b = next(s for s in b["segments"] if s["name"] == "Seg B")

    # Update
    upd = client.patch(
        f"/api/talent-market-maps/{map_id}/segments/{seg_a['id']}",
        json={"priority": "high", "coverage_status": "covered"},
    ).json()
    seg_a_upd = next(s for s in upd["segments"] if s["id"] == seg_a["id"])
    assert seg_a_upd["priority"] == "high"
    assert seg_a_upd["coverage_status"] == "covered"

    # Reorder: B antes que A
    reordered = client.patch(
        f"/api/talent-market-maps/{map_id}/segments/reorder",
        json={"ordered_ids": [seg_b["id"], seg_a["id"]]},
    ).json()
    assert [s["id"] for s in reordered["segments"]] == [seg_b["id"], seg_a["id"]]

    # Delete
    after_del = client.delete(
        f"/api/talent-market-maps/{map_id}/segments/{seg_a['id']}"
    ).json()
    assert seg_a["id"] not in [s["id"] for s in after_del["segments"]]

    # Delete inexistente → 404
    assert client.delete(f"/api/talent-market-maps/{map_id}/segments/999999").status_code == 404


def test_company_and_role_crud(client, session_factory):
    mandate_id, _ = _seed_mandate_with_spec(session_factory)
    map_id = client.get(f"/api/mandatos/{mandate_id}/talent-market-map").json()["id"]

    co = client.post(
        f"/api/talent-market-maps/{map_id}/companies",
        json={"name": "Cencosud", "industry": "Retail", "priority": "high"},
    ).json()
    company = next(c for c in co["companies"] if c["name"] == "Cencosud")
    assert company["industry"] == "Retail"

    client.patch(
        f"/api/talent-market-maps/{map_id}/companies/{company['id']}",
        json={"coverage_status": "covered"},
    )

    role = client.post(
        f"/api/talent-market-maps/{map_id}/equivalent-roles",
        json={"title": "Director Comercial", "closeness": "high", "industries": ["Retail"]},
    ).json()
    r = next(x for x in role["equivalent_roles"] if x["title"] == "Director Comercial")
    assert r["industries"] == ["Retail"]

    # Deletes
    assert (
        client.delete(f"/api/talent-market-maps/{map_id}/companies/{company['id']}").status_code
        == 200
    )
    assert (
        client.delete(
            f"/api/talent-market-maps/{map_id}/equivalent-roles/{r['id']}"
        ).status_code
        == 200
    )


# ===========================================================================
# API: gaps recompute + recommendations + decisión
# ===========================================================================


def test_recompute_gaps_from_evaluations(client, session_factory):
    mandate_id, spec_id = _seed_mandate_with_spec(session_factory)
    map_id = client.get(f"/api/mandatos/{mandate_id}/talent-market-map").json()["id"]

    gap = [{"requirement": "Inglés avanzado", "reason": "No certifica", "impact": "high"}]
    _add_candidate_with_eval(session_factory, mandate_id, spec_id, name="A", company="X", score=50, critical_gaps=gap)
    _add_candidate_with_eval(session_factory, mandate_id, spec_id, name="B", company="Y", score=48, critical_gaps=gap)
    _add_candidate_with_eval(session_factory, mandate_id, spec_id, name="C", company="Z", score=52, critical_gaps=gap)

    body = client.post(f"/api/talent-market-maps/{map_id}/gaps/recompute").json()
    assert len(body["gaps"]) == 1
    g = body["gaps"][0]
    assert g["frequency"] == 3
    assert g["total_evaluated"] == 3
    assert g["impact"] == "high"


def test_recommendations_regenerate_and_decide(client, session_factory):
    mandate_id, spec_id = _seed_mandate_with_spec(session_factory)
    map_id = client.get(f"/api/mandatos/{mandate_id}/talent-market-map").json()["id"]

    # Pipeline sin evaluación → dispara R6
    with session_factory() as db:
        cand = Candidate(full_name="Sin Eval", current_position="x", current_company="x")
        db.add(cand)
        db.flush()
        db.add(
            CandidatePipelineItem(
                mandate_id=mandate_id, candidate_id=cand.id, evaluation_id=None, stage="received"
            )
        )
        db.commit()

    body = client.post(
        f"/api/talent-market-maps/{map_id}/recommendations/regenerate"
    ).json()
    assert len(body["recommendations"]) >= 1
    rec = body["recommendations"][0]
    assert rec["status"] == "suggested"

    # Aceptar
    decided = client.patch(
        f"/api/talent-market-maps/{map_id}/recommendations/{rec['id']}",
        json={"status": "accepted"},
    ).json()
    accepted = next(r for r in decided["recommendations"] if r["id"] == rec["id"])
    assert accepted["status"] == "accepted"
    assert accepted["acted_at"] is not None

    # Regenerar de nuevo no borra la aceptada
    again = client.post(
        f"/api/talent-market-maps/{map_id}/recommendations/regenerate"
    ).json()
    assert any(
        r["id"] == rec["id"] and r["status"] == "accepted" for r in again["recommendations"]
    )


# ===========================================================================
# API: asignación de candidatos + cobertura derivada
# ===========================================================================


def test_candidate_assignment_and_company_counts(client, session_factory):
    mandate_id, spec_id = _seed_mandate_with_spec(session_factory)
    map_id = client.get(f"/api/mandatos/{mandate_id}/talent-market-map").json()["id"]

    # Candidato cuya empresa coincide con la target company → auto-match
    cand_id, _ = _add_candidate_with_eval(
        session_factory, mandate_id, spec_id, name="Match Auto", company="Falabella", score=80
    )
    co = client.post(
        f"/api/talent-market-maps/{map_id}/companies",
        json={"name": "Falabella", "industry": "Retail"},
    ).json()
    company = next(c for c in co["companies"] if c["name"] == "Falabella")
    assert company["candidates_identified"] == 1
    assert company["candidates_evaluated"] == 1
    assert company["high_fit_candidates"] == 1  # score 80 >= 70

    # Asignación manual a un cargo equivalente
    role = client.post(
        f"/api/talent-market-maps/{map_id}/equivalent-roles",
        json={"title": "Head Comercial"},
    ).json()
    role_id = role["equivalent_roles"][0]["id"]
    assigned = client.post(
        f"/api/talent-market-maps/{map_id}/candidates/{cand_id}/assign",
        json={"equivalent_role_id": role_id},
    ).json()
    assigned_role = next(r for r in assigned["equivalent_roles"] if r["id"] == role_id)
    assert assigned_role["candidate_count"] == 1

    # Unassign
    client.delete(f"/api/talent-market-maps/{map_id}/candidates/{cand_id}/assign")


def test_list_candidates_overview(client, session_factory):
    mandate_id, spec_id = _seed_mandate_with_spec(session_factory)
    map_id = client.get(f"/api/mandatos/{mandate_id}/talent-market-map").json()["id"]

    cand_id, _ = _add_candidate_with_eval(
        session_factory, mandate_id, spec_id, name="Auto Match", company="Falabella", score=82
    )
    # Empresa target con mismo nombre → debe reportarse como auto_company_id
    co = client.post(
        f"/api/talent-market-maps/{map_id}/companies",
        json={"name": "Falabella", "industry": "Retail"},
    ).json()
    company_id = next(c for c in co["companies"] if c["name"] == "Falabella")["id"]

    overview = client.get(f"/api/talent-market-maps/{map_id}/candidates").json()
    assert len(overview) == 1
    row = overview[0]
    assert row["candidate_id"] == cand_id
    assert row["full_name"] == "Auto Match"
    assert row["evaluation_score"] == 82
    assert row["auto_company_id"] == company_id
    assert row["segment_id"] is None  # sin override aún

    # Tras asignar manualmente a un segmento, aparece en el override
    seg = client.post(
        f"/api/talent-market-maps/{map_id}/segments",
        json={"name": "Retail directo", "segment_type": "primary"},
    ).json()
    seg_id = seg["segments"][0]["id"]
    client.post(
        f"/api/talent-market-maps/{map_id}/candidates/{cand_id}/assign",
        json={"segment_id": seg_id},
    )
    overview2 = client.get(f"/api/talent-market-maps/{map_id}/candidates").json()
    assert overview2[0]["segment_id"] == seg_id


def test_coverage_stats(client, session_factory):
    mandate_id, spec_id = _seed_mandate_with_spec(session_factory)
    map_id = client.get(f"/api/mandatos/{mandate_id}/talent-market-map").json()["id"]

    _add_candidate_with_eval(session_factory, mandate_id, spec_id, name="Hi", company="A", score=85)
    _add_candidate_with_eval(session_factory, mandate_id, spec_id, name="Mid", company="B", score=60)
    _add_candidate_with_eval(
        session_factory, mandate_id, spec_id, name="Disc", company="C", score=30, stage="discarded"
    )

    cov = client.get(f"/api/mandatos/{mandate_id}/talent-market-map").json()["coverage"]
    assert cov["candidates_identified"] == 3
    assert cov["candidates_evaluated"] == 3
    assert cov["high_fit"] == 1
    assert cov["medium_fit"] == 1
    assert cov["low_fit"] == 1
    assert cov["discarded"] == 1
    assert cov["coverage_pct"] > 0


# ===========================================================================
# API: export + archive
# ===========================================================================


def test_export_summary_plaintext(client, session_factory, monkeypatch):
    import app.services.talent_market_map_service as svc

    monkeypatch.setattr(svc, "generate_talent_market_map", lambda mandate, spec: _fake_payload())

    mandate_id, _ = _seed_mandate_with_spec(session_factory)
    map_id = client.get(f"/api/mandatos/{mandate_id}/talent-market-map").json()["id"]
    client.post(f"/api/mandatos/{mandate_id}/talent-market-map/generate")

    resp = client.get(f"/api/talent-market-maps/{map_id}/export/summary")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    text = resp.text
    assert "Talent Market Map" in text
    assert "Resumen ejecutivo" in text
    assert "Retail directo" in text  # segmento generado
    assert "Falabella" in text  # empresa generada


def test_archive_map(client, session_factory):
    mandate_id, _ = _seed_mandate_with_spec(session_factory)
    map_id = client.get(f"/api/mandatos/{mandate_id}/talent-market-map").json()["id"]

    assert client.delete(f"/api/talent-market-maps/{map_id}").status_code == 204
    body = client.get(f"/api/mandatos/{mandate_id}/talent-market-map").json()
    assert body["status"] == "archived"

    # Archivar inexistente → 404
    assert client.delete("/api/talent-market-maps/999999").status_code == 404
