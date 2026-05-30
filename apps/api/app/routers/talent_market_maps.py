"""Rutas del Talent Market Map.

Admin (sin auth en MVP, igual que el resto):
    GET    /api/mandatos/{mandate_id}/talent-market-map        — get-or-create
    POST   /api/mandatos/{mandate_id}/talent-market-map/generate
    PATCH  /api/talent-market-maps/{id}                        — editar resumen, status
    DELETE /api/talent-market-maps/{id}                        — archivar
    POST   /api/talent-market-maps/{id}/segments
    PATCH  /api/talent-market-maps/{id}/segments/{seg_id}
    DELETE /api/talent-market-maps/{id}/segments/{seg_id}
    PATCH  /api/talent-market-maps/{id}/segments/reorder
    POST   /api/talent-market-maps/{id}/companies
    PATCH  /api/talent-market-maps/{id}/companies/{co_id}
    DELETE /api/talent-market-maps/{id}/companies/{co_id}
    POST   /api/talent-market-maps/{id}/equivalent-roles
    PATCH  /api/talent-market-maps/{id}/equivalent-roles/{role_id}
    DELETE /api/talent-market-maps/{id}/equivalent-roles/{role_id}
    POST   /api/talent-market-maps/{id}/gaps/recompute
    POST   /api/talent-market-maps/{id}/recommendations/regenerate
    PATCH  /api/talent-market-maps/{id}/recommendations/{rec_id}
    POST   /api/talent-market-maps/{id}/candidates/{cand_id}/assign
    DELETE /api/talent-market-maps/{id}/candidates/{cand_id}/assign
    GET    /api/talent-market-maps/{id}/export/summary
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.talent_market_map import (
    CandidateAssignPayload,
    CompanyCreatePayload,
    CompanyUpdatePayload,
    EquivalentRoleCreatePayload,
    EquivalentRoleUpdatePayload,
    GenerateMapPayload,
    MapCandidateRead,
    MapUpdatePayload,
    RecommendationDecisionPayload,
    SegmentCreatePayload,
    SegmentReorderPayload,
    SegmentUpdatePayload,
    TalentMarketMapRead,
    TalentMarketMapSummary,
)
from app.services.talent_market_map_service import TalentMarketMapService

router = APIRouter(tags=["talent-market-map"])


def _serialize(service: TalentMarketMapService, map_) -> dict:
    coverage = service.compute_coverage(map_.search_mandate_id, map_.id)
    candidate_counts_by_segment = service.candidate_counts_by_segment(
        map_.id, map_.search_mandate_id
    )
    candidate_counts_by_company = service.candidate_counts_by_company(
        map_.id, map_.search_mandate_id
    )
    candidate_counts_by_role = service.candidate_counts_by_equivalent_role(
        map_.id, map_.search_mandate_id
    )

    segments = [
        {
            "id": s.id,
            "market_map_id": s.market_map_id,
            "name": s.name,
            "segment_type": s.segment_type,
            "description": s.description,
            "priority": s.priority,
            "coverage_status": s.coverage_status,
            "rationale": s.rationale,
            "sort_order": s.sort_order,
            "ai_suggested": s.ai_suggested,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
            "candidate_count": candidate_counts_by_segment.get(s.id, 0),
        }
        for s in service.list_segments(map_.id)
    ]
    companies = [
        {
            "id": c.id,
            "market_map_id": c.market_map_id,
            "segment_id": c.segment_id,
            "name": c.name,
            "industry": c.industry,
            "priority": c.priority,
            "rationale": c.rationale,
            "coverage_status": c.coverage_status,
            "notes": c.notes,
            "ai_suggested": c.ai_suggested,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
            "candidates_identified": candidate_counts_by_company.get(c.id, {}).get(
                "identified", 0
            ),
            "candidates_evaluated": candidate_counts_by_company.get(c.id, {}).get(
                "evaluated", 0
            ),
            "high_fit_candidates": candidate_counts_by_company.get(c.id, {}).get(
                "high_fit", 0
            ),
        }
        for c in service.list_companies(map_.id)
    ]
    roles = [
        {
            "id": r.id,
            "market_map_id": r.market_map_id,
            "title": r.title,
            "seniority": r.seniority,
            "closeness": r.closeness,
            "rationale": r.rationale,
            "priority": r.priority,
            "industries": list(r.industries or []),
            "ai_suggested": r.ai_suggested,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
            "candidate_count": candidate_counts_by_role.get(r.id, 0),
        }
        for r in service.list_equivalent_roles(map_.id)
    ]
    gaps = [
        {
            "id": g.id,
            "market_map_id": g.market_map_id,
            "title": g.title,
            "frequency": g.frequency,
            "total_evaluated": g.total_evaluated,
            "impact": g.impact,
            "evidence": g.evidence,
            "recommendation": g.recommendation,
            "detected_at": g.detected_at,
        }
        for g in service.list_gaps(map_.id)
    ]
    recommendations = [
        {
            "id": r.id,
            "market_map_id": r.market_map_id,
            "title": r.title,
            "reason": r.reason,
            "expected_impact": r.expected_impact,
            "confidence": r.confidence,
            "status": r.status,
            "generated_by": r.generated_by,
            "acted_at": r.acted_at,
            "created_at": r.created_at,
        }
        for r in service.list_recommendations(map_.id)
    ]

    return {
        "id": map_.id,
        "search_mandate_id": map_.search_mandate_id,
        "position_spec_id": map_.position_spec_id,
        "status": map_.status,
        "executive_summary": map_.executive_summary,
        "executive_summary_for_client": map_.executive_summary_for_client,
        "market_assessment": map_.market_assessment,
        "generated_by_model": map_.generated_by_model,
        "prompt_version": map_.prompt_version,
        "generated_at": map_.generated_at,
        "created_at": map_.created_at,
        "updated_at": map_.updated_at,
        "segments": segments,
        "companies": companies,
        "equivalent_roles": roles,
        "gaps": gaps,
        "recommendations": recommendations,
        "coverage": coverage,
    }


# --- Map maestro -----------------------------------------------------------


@router.get(
    "/api/talent-market-maps",
    response_model=list[TalentMarketMapSummary],
)
def list_maps(db: Session = Depends(get_db)) -> list[dict]:
    return TalentMarketMapService(db).list_all_summaries()


@router.get(
    "/api/mandatos/{mandate_id}/talent-market-map",
    response_model=TalentMarketMapRead,
)
def get_or_create_map(mandate_id: int, db: Session = Depends(get_db)) -> dict:
    service = TalentMarketMapService(db)
    try:
        map_ = service.get_or_create_for_mandate(mandate_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return _serialize(service, map_)


@router.post(
    "/api/mandatos/{mandate_id}/talent-market-map/generate",
    response_model=TalentMarketMapRead,
)
def generate_map(
    mandate_id: int,
    payload: GenerateMapPayload | None = None,
    db: Session = Depends(get_db),
) -> dict:
    service = TalentMarketMapService(db)
    try:
        map_ = service.get_or_create_for_mandate(mandate_id)
        opts = payload or GenerateMapPayload()
        map_ = service.generate_map_content(
            map_.id,
            overwrite_ai_suggested=opts.overwrite_ai_suggested,
            overwrite_manual=opts.overwrite_manual,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    # Después de generar, recalcula brechas + recomendaciones automáticamente
    service.recompute_gaps(map_.id)
    service.regenerate_recommendations(map_.id)
    return _serialize(service, service.get(map_.id))


@router.patch(
    "/api/talent-market-maps/{map_id}", response_model=TalentMarketMapRead
)
def update_map(
    map_id: int, payload: MapUpdatePayload, db: Session = Depends(get_db)
) -> dict:
    service = TalentMarketMapService(db)
    map_ = service.update_map(map_id, payload.model_dump(exclude_unset=True))
    if map_ is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Talent Market Map no encontrado"
        )
    return _serialize(service, map_)


@router.delete(
    "/api/talent-market-maps/{map_id}", status_code=status.HTTP_204_NO_CONTENT
)
def archive_map(map_id: int, db: Session = Depends(get_db)) -> None:
    service = TalentMarketMapService(db)
    if not service.archive(map_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Talent Market Map no encontrado"
        )


# --- Segments --------------------------------------------------------------


@router.post(
    "/api/talent-market-maps/{map_id}/segments", response_model=TalentMarketMapRead
)
def add_segment(
    map_id: int, payload: SegmentCreatePayload, db: Session = Depends(get_db)
) -> dict:
    service = TalentMarketMapService(db)
    if service.get(map_id) is None:
        raise HTTPException(status_code=404, detail="Talent Market Map no encontrado")
    service.add_segment(map_id, payload.model_dump(), ai_suggested=False)
    return _serialize(service, service.get(map_id))


@router.patch(
    "/api/talent-market-maps/{map_id}/segments/reorder",
    response_model=TalentMarketMapRead,
)
def reorder_segments(
    map_id: int, payload: SegmentReorderPayload, db: Session = Depends(get_db)
) -> dict:
    service = TalentMarketMapService(db)
    if service.get(map_id) is None:
        raise HTTPException(status_code=404, detail="Talent Market Map no encontrado")
    service.reorder_segments(map_id, payload.ordered_ids)
    return _serialize(service, service.get(map_id))


@router.patch(
    "/api/talent-market-maps/{map_id}/segments/{seg_id}",
    response_model=TalentMarketMapRead,
)
def update_segment(
    map_id: int,
    seg_id: int,
    payload: SegmentUpdatePayload,
    db: Session = Depends(get_db),
) -> dict:
    service = TalentMarketMapService(db)
    seg = service.update_segment(map_id, seg_id, payload.model_dump(exclude_unset=True))
    if seg is None:
        raise HTTPException(status_code=404, detail="Segmento no encontrado")
    return _serialize(service, service.get(map_id))


@router.delete(
    "/api/talent-market-maps/{map_id}/segments/{seg_id}",
    response_model=TalentMarketMapRead,
)
def delete_segment(
    map_id: int, seg_id: int, db: Session = Depends(get_db)
) -> dict:
    service = TalentMarketMapService(db)
    if not service.delete_segment(map_id, seg_id):
        raise HTTPException(status_code=404, detail="Segmento no encontrado")
    return _serialize(service, service.get(map_id))


# --- Companies -------------------------------------------------------------


@router.post(
    "/api/talent-market-maps/{map_id}/companies", response_model=TalentMarketMapRead
)
def add_company(
    map_id: int, payload: CompanyCreatePayload, db: Session = Depends(get_db)
) -> dict:
    service = TalentMarketMapService(db)
    if service.get(map_id) is None:
        raise HTTPException(status_code=404, detail="Talent Market Map no encontrado")
    service.add_company(map_id, payload.model_dump(), ai_suggested=False)
    return _serialize(service, service.get(map_id))


@router.patch(
    "/api/talent-market-maps/{map_id}/companies/{co_id}",
    response_model=TalentMarketMapRead,
)
def update_company(
    map_id: int,
    co_id: int,
    payload: CompanyUpdatePayload,
    db: Session = Depends(get_db),
) -> dict:
    service = TalentMarketMapService(db)
    co = service.update_company(map_id, co_id, payload.model_dump(exclude_unset=True))
    if co is None:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return _serialize(service, service.get(map_id))


@router.delete(
    "/api/talent-market-maps/{map_id}/companies/{co_id}",
    response_model=TalentMarketMapRead,
)
def delete_company(
    map_id: int, co_id: int, db: Session = Depends(get_db)
) -> dict:
    service = TalentMarketMapService(db)
    if not service.delete_company(map_id, co_id):
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return _serialize(service, service.get(map_id))


# --- Equivalent roles ------------------------------------------------------


@router.post(
    "/api/talent-market-maps/{map_id}/equivalent-roles",
    response_model=TalentMarketMapRead,
)
def add_equivalent_role(
    map_id: int,
    payload: EquivalentRoleCreatePayload,
    db: Session = Depends(get_db),
) -> dict:
    service = TalentMarketMapService(db)
    if service.get(map_id) is None:
        raise HTTPException(status_code=404, detail="Talent Market Map no encontrado")
    service.add_equivalent_role(map_id, payload.model_dump(), ai_suggested=False)
    return _serialize(service, service.get(map_id))


@router.patch(
    "/api/talent-market-maps/{map_id}/equivalent-roles/{role_id}",
    response_model=TalentMarketMapRead,
)
def update_equivalent_role(
    map_id: int,
    role_id: int,
    payload: EquivalentRoleUpdatePayload,
    db: Session = Depends(get_db),
) -> dict:
    service = TalentMarketMapService(db)
    role = service.update_equivalent_role(
        map_id, role_id, payload.model_dump(exclude_unset=True)
    )
    if role is None:
        raise HTTPException(status_code=404, detail="Cargo equivalente no encontrado")
    return _serialize(service, service.get(map_id))


@router.delete(
    "/api/talent-market-maps/{map_id}/equivalent-roles/{role_id}",
    response_model=TalentMarketMapRead,
)
def delete_equivalent_role(
    map_id: int, role_id: int, db: Session = Depends(get_db)
) -> dict:
    service = TalentMarketMapService(db)
    if not service.delete_equivalent_role(map_id, role_id):
        raise HTTPException(status_code=404, detail="Cargo equivalente no encontrado")
    return _serialize(service, service.get(map_id))


# --- Gaps + Recommendations ------------------------------------------------


@router.post(
    "/api/talent-market-maps/{map_id}/gaps/recompute",
    response_model=TalentMarketMapRead,
)
def recompute_gaps(map_id: int, db: Session = Depends(get_db)) -> dict:
    service = TalentMarketMapService(db)
    try:
        service.recompute_gaps(map_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return _serialize(service, service.get(map_id))


@router.post(
    "/api/talent-market-maps/{map_id}/recommendations/regenerate",
    response_model=TalentMarketMapRead,
)
def regenerate_recommendations(
    map_id: int, db: Session = Depends(get_db)
) -> dict:
    service = TalentMarketMapService(db)
    try:
        service.regenerate_recommendations(map_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return _serialize(service, service.get(map_id))


@router.patch(
    "/api/talent-market-maps/{map_id}/recommendations/{rec_id}",
    response_model=TalentMarketMapRead,
)
def decide_recommendation(
    map_id: int,
    rec_id: int,
    payload: RecommendationDecisionPayload,
    db: Session = Depends(get_db),
) -> dict:
    service = TalentMarketMapService(db)
    rec = service.update_recommendation_status(map_id, rec_id, payload.status)
    if rec is None:
        raise HTTPException(status_code=404, detail="Recomendación no encontrada")
    return _serialize(service, service.get(map_id))


# --- Candidates ------------------------------------------------------------


@router.get(
    "/api/talent-market-maps/{map_id}/candidates",
    response_model=list[MapCandidateRead],
)
def list_map_candidates(map_id: int, db: Session = Depends(get_db)) -> list[dict]:
    service = TalentMarketMapService(db)
    map_ = service.get(map_id)
    if map_ is None:
        raise HTTPException(status_code=404, detail="Talent Market Map no encontrado")
    return service.list_candidates_overview(map_id, map_.search_mandate_id)


@router.post(
    "/api/talent-market-maps/{map_id}/candidates/{cand_id}/assign",
    response_model=TalentMarketMapRead,
)
def assign_candidate(
    map_id: int,
    cand_id: int,
    payload: CandidateAssignPayload,
    db: Session = Depends(get_db),
) -> dict:
    service = TalentMarketMapService(db)
    if service.get(map_id) is None:
        raise HTTPException(status_code=404, detail="Talent Market Map no encontrado")
    service.assign_candidate(
        map_id=map_id,
        candidate_id=cand_id,
        segment_id=payload.segment_id,
        target_company_id=payload.target_company_id,
        equivalent_role_id=payload.equivalent_role_id,
    )
    return _serialize(service, service.get(map_id))


@router.delete(
    "/api/talent-market-maps/{map_id}/candidates/{cand_id}/assign",
    response_model=TalentMarketMapRead,
)
def unassign_candidate(
    map_id: int, cand_id: int, db: Session = Depends(get_db)
) -> dict:
    service = TalentMarketMapService(db)
    if service.get(map_id) is None:
        raise HTTPException(status_code=404, detail="Talent Market Map no encontrado")
    service.unassign_candidate(map_id, cand_id)
    return _serialize(service, service.get(map_id))


# --- Export ----------------------------------------------------------------


@router.get(
    "/api/talent-market-maps/{map_id}/export/summary",
    response_class=PlainTextResponse,
)
def export_summary(map_id: int, db: Session = Depends(get_db)) -> str:
    service = TalentMarketMapService(db)
    map_ = service.get(map_id)
    if map_ is None:
        raise HTTPException(status_code=404, detail="Talent Market Map no encontrado")
    coverage = service.compute_coverage(map_.search_mandate_id, map_id)

    lines: list[str] = []
    lines.append(f"# Talent Market Map · Mandato {map_.search_mandate_id}")
    lines.append("")
    if map_.executive_summary:
        lines.append("## Resumen ejecutivo")
        lines.append(map_.executive_summary)
        lines.append("")
    lines.append("## Cobertura")
    lines.append(f"- Cobertura general: {coverage['coverage_pct']}%")
    lines.append(
        f"- Candidatos: {coverage['candidates_identified']} identificados · "
        f"{coverage['candidates_evaluated']} evaluados · "
        f"{coverage['high_fit']} alto calce · "
        f"{coverage['shortlisted']} en shortlist"
    )
    lines.append(
        f"- Empresas target: {coverage['target_companies_total']} totales · "
        f"{coverage['target_companies_reviewed']} revisadas · "
        f"{coverage['target_companies_pending']} pendientes"
    )
    lines.append(f"- Industrias cubiertas: {coverage['industries_covered']}")
    lines.append("")

    segments = service.list_segments(map_id)
    if segments:
        lines.append("## Segmentos de mercado")
        for s in segments:
            lines.append(f"- [{s.segment_type}] {s.name} ({s.priority}) — {s.coverage_status}")
            if s.description:
                lines.append(f"  {s.description}")
        lines.append("")

    companies = service.list_companies(map_id)
    if companies:
        lines.append("## Empresas target")
        for c in companies:
            ind = f" · {c.industry}" if c.industry else ""
            lines.append(f"- {c.name}{ind} ({c.priority}) — {c.coverage_status}")
        lines.append("")

    roles = service.list_equivalent_roles(map_id)
    if roles:
        lines.append("## Cargos equivalentes")
        for r in roles:
            sen = f" · {r.seniority}" if r.seniority else ""
            lines.append(f"- {r.title}{sen} (cercanía: {r.closeness}, prioridad: {r.priority})")
        lines.append("")

    gaps = service.list_gaps(map_id)
    if gaps:
        lines.append("## Brechas detectadas")
        for g in gaps:
            lines.append(
                f"- {g.title}: {g.frequency}/{g.total_evaluated} candidatos "
                f"(impacto {g.impact})"
            )
            if g.recommendation:
                lines.append(f"  → {g.recommendation}")
        lines.append("")

    recs = service.list_recommendations(map_id)
    accepted = [r for r in recs if r.status == "accepted"]
    if accepted:
        lines.append("## Recomendaciones aceptadas")
        for r in accepted:
            lines.append(f"- {r.title} (confianza {r.confidence})")
            lines.append(f"  Razón: {r.reason}")
        lines.append("")

    return "\n".join(lines)
