"""Servicio del Talent Market Map.

Responsabilidades:
- CRUD del mapa, segmentos, empresas, cargos equivalentes
- Cobertura calculada en tiempo real desde pipeline + evaluaciones + shortlists
- Asignación manual de candidatos
- Wrapper para generación IA (delega en `app/ai/talent_market_map_generator.py`)
- Wrapper para análisis determinístico (delega en `app/scoring/gap_detector.py` y
  `app/scoring/recommendation_engine.py`)
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.candidate_evaluation import CandidateEvaluation
from app.models.candidate_pipeline_item import CandidatePipelineItem
from app.models.candidate_profile import CandidateProfile
from app.models.client_shortlist import ClientShortlist, ClientShortlistItem
from app.models.position_spec import PositionSpec
from app.models.search_mandate import SearchMandate
from app.ai.talent_market_map_generator import generate_talent_market_map
from app.models.talent_market_map import (
    EquivalentRole,
    MarketGap,
    MarketMapCandidateOverride,
    MarketSegment,
    RecalibrationRecommendation,
    TalentMarketMap,
    TargetCompany,
)
from app.scoring.gap_detector import detect_gaps
from app.scoring.recommendation_engine import generate_rule_recommendations


# --- Helpers de normalización ---------------------------------------------


def _norm(value: str | None) -> str:
    return (value or "").strip().casefold()


# --- Service ---------------------------------------------------------------


class TalentMarketMapService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- CRUD mapa --------------------------------------------------------

    def get_by_mandate(self, mandate_id: int) -> TalentMarketMap | None:
        return self.db.scalars(
            select(TalentMarketMap).where(
                TalentMarketMap.search_mandate_id == mandate_id
            )
        ).first()

    def get_or_create_for_mandate(self, mandate_id: int) -> TalentMarketMap:
        mandate = self.db.get(SearchMandate, mandate_id)
        if mandate is None:
            raise ValueError("Mandato no encontrado")
        existing = self.get_by_mandate(mandate_id)
        if existing is not None:
            return existing
        # Crea vacío en draft. La generación IA es explícita por endpoint /generate.
        position_spec = self.db.scalars(
            select(PositionSpec)
            .where(PositionSpec.search_mandate_id == mandate_id)
            .order_by(PositionSpec.created_at.desc())
        ).first()
        map_ = TalentMarketMap(
            search_mandate_id=mandate_id,
            position_spec_id=position_spec.id if position_spec else None,
            status="draft",
        )
        self.db.add(map_)
        self.db.commit()
        self.db.refresh(map_)
        return map_

    def get(self, map_id: int) -> TalentMarketMap | None:
        return self.db.get(TalentMarketMap, map_id)

    def update_map(
        self, map_id: int, patch: dict[str, Any]
    ) -> TalentMarketMap | None:
        map_ = self.get(map_id)
        if map_ is None:
            return None
        for key, value in patch.items():
            if value is None:
                continue
            if hasattr(map_, key):
                setattr(map_, key, value)
        self.db.add(map_)
        self.db.commit()
        self.db.refresh(map_)
        return map_

    def archive(self, map_id: int) -> bool:
        map_ = self.get(map_id)
        if map_ is None:
            return False
        map_.status = "archived"
        self.db.add(map_)
        self.db.commit()
        return True

    # --- Segments --------------------------------------------------------

    def list_segments(self, map_id: int) -> list[MarketSegment]:
        return list(
            self.db.scalars(
                select(MarketSegment)
                .where(MarketSegment.market_map_id == map_id)
                .order_by(MarketSegment.sort_order.asc(), MarketSegment.id.asc())
            ).all()
        )

    def add_segment(
        self, map_id: int, payload: dict[str, Any], ai_suggested: bool = False
    ) -> MarketSegment:
        next_order = max(
            (s.sort_order for s in self.list_segments(map_id)), default=-1
        ) + 1
        seg = MarketSegment(
            market_map_id=map_id,
            sort_order=next_order,
            ai_suggested=ai_suggested,
            **payload,
        )
        self.db.add(seg)
        self.db.commit()
        self.db.refresh(seg)
        return seg

    def update_segment(
        self, map_id: int, seg_id: int, patch: dict[str, Any]
    ) -> MarketSegment | None:
        seg = self.db.get(MarketSegment, seg_id)
        if seg is None or seg.market_map_id != map_id:
            return None
        for key, value in patch.items():
            if value is None:
                continue
            if hasattr(seg, key):
                setattr(seg, key, value)
        self.db.add(seg)
        self.db.commit()
        self.db.refresh(seg)
        return seg

    def delete_segment(self, map_id: int, seg_id: int) -> bool:
        seg = self.db.get(MarketSegment, seg_id)
        if seg is None or seg.market_map_id != map_id:
            return False
        self.db.delete(seg)
        self.db.commit()
        return True

    def reorder_segments(self, map_id: int, ordered_ids: list[int]) -> None:
        segs = {s.id: s for s in self.list_segments(map_id)}
        for index, sid in enumerate(ordered_ids):
            seg = segs.get(sid)
            if seg is not None and seg.sort_order != index:
                seg.sort_order = index
                self.db.add(seg)
        self.db.commit()

    # --- Companies -------------------------------------------------------

    def list_companies(self, map_id: int) -> list[TargetCompany]:
        return list(
            self.db.scalars(
                select(TargetCompany)
                .where(TargetCompany.market_map_id == map_id)
                .order_by(TargetCompany.priority.desc(), TargetCompany.id.asc())
            ).all()
        )

    def add_company(
        self, map_id: int, payload: dict[str, Any], ai_suggested: bool = False
    ) -> TargetCompany:
        company = TargetCompany(
            market_map_id=map_id, ai_suggested=ai_suggested, **payload
        )
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return company

    def update_company(
        self, map_id: int, co_id: int, patch: dict[str, Any]
    ) -> TargetCompany | None:
        company = self.db.get(TargetCompany, co_id)
        if company is None or company.market_map_id != map_id:
            return None
        for key, value in patch.items():
            if value is None:
                continue
            if hasattr(company, key):
                setattr(company, key, value)
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return company

    def delete_company(self, map_id: int, co_id: int) -> bool:
        company = self.db.get(TargetCompany, co_id)
        if company is None or company.market_map_id != map_id:
            return False
        self.db.delete(company)
        self.db.commit()
        return True

    # --- Equivalent roles -----------------------------------------------

    def list_equivalent_roles(self, map_id: int) -> list[EquivalentRole]:
        return list(
            self.db.scalars(
                select(EquivalentRole)
                .where(EquivalentRole.market_map_id == map_id)
                .order_by(
                    EquivalentRole.closeness.desc(),
                    EquivalentRole.id.asc(),
                )
            ).all()
        )

    def add_equivalent_role(
        self, map_id: int, payload: dict[str, Any], ai_suggested: bool = False
    ) -> EquivalentRole:
        role = EquivalentRole(
            market_map_id=map_id, ai_suggested=ai_suggested, **payload
        )
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def update_equivalent_role(
        self, map_id: int, role_id: int, patch: dict[str, Any]
    ) -> EquivalentRole | None:
        role = self.db.get(EquivalentRole, role_id)
        if role is None or role.market_map_id != map_id:
            return None
        for key, value in patch.items():
            if value is None:
                continue
            if hasattr(role, key):
                setattr(role, key, value)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def delete_equivalent_role(self, map_id: int, role_id: int) -> bool:
        role = self.db.get(EquivalentRole, role_id)
        if role is None or role.market_map_id != map_id:
            return False
        self.db.delete(role)
        self.db.commit()
        return True

    # --- Gaps + recommendations (escritos por engines) -------------------

    def list_gaps(self, map_id: int) -> list[MarketGap]:
        return list(
            self.db.scalars(
                select(MarketGap)
                .where(MarketGap.market_map_id == map_id)
                .order_by(MarketGap.frequency.desc(), MarketGap.id.asc())
            ).all()
        )

    def replace_gaps(self, map_id: int, gaps_data: list[dict[str, Any]]) -> None:
        # Borra existentes
        for g in self.list_gaps(map_id):
            self.db.delete(g)
        self.db.flush()
        for data in gaps_data:
            self.db.add(MarketGap(market_map_id=map_id, **data))
        self.db.commit()

    def list_recommendations(
        self, map_id: int, include_acted: bool = True
    ) -> list[RecalibrationRecommendation]:
        query = select(RecalibrationRecommendation).where(
            RecalibrationRecommendation.market_map_id == map_id
        )
        if not include_acted:
            query = query.where(RecalibrationRecommendation.status == "suggested")
        return list(
            self.db.scalars(query.order_by(RecalibrationRecommendation.id.asc())).all()
        )

    def replace_suggested_recommendations(
        self, map_id: int, recs_data: list[dict[str, Any]]
    ) -> None:
        """Reemplaza sólo las recomendaciones con status=suggested.

        Las accepted/rejected se preservan para no perder decisiones del consultor.
        """
        for r in self.list_recommendations(map_id, include_acted=True):
            if r.status == "suggested":
                self.db.delete(r)
        self.db.flush()
        for data in recs_data:
            self.db.add(RecalibrationRecommendation(market_map_id=map_id, **data))
        self.db.commit()

    def update_recommendation_status(
        self, map_id: int, rec_id: int, status: str
    ) -> RecalibrationRecommendation | None:
        rec = self.db.get(RecalibrationRecommendation, rec_id)
        if rec is None or rec.market_map_id != map_id:
            return None
        rec.status = status
        rec.acted_at = datetime.now(timezone.utc)
        self.db.add(rec)
        self.db.commit()
        self.db.refresh(rec)
        return rec

    # --- Candidate overrides --------------------------------------------

    def assign_candidate(
        self,
        map_id: int,
        candidate_id: int,
        segment_id: int | None,
        target_company_id: int | None,
        equivalent_role_id: int | None,
    ) -> MarketMapCandidateOverride:
        existing = self.db.scalars(
            select(MarketMapCandidateOverride).where(
                MarketMapCandidateOverride.market_map_id == map_id,
                MarketMapCandidateOverride.candidate_id == candidate_id,
            )
        ).first()
        if existing is None:
            existing = MarketMapCandidateOverride(
                market_map_id=map_id, candidate_id=candidate_id
            )
        existing.segment_id = segment_id
        existing.target_company_id = target_company_id
        existing.equivalent_role_id = equivalent_role_id
        self.db.add(existing)
        self.db.commit()
        self.db.refresh(existing)
        return existing

    def unassign_candidate(self, map_id: int, candidate_id: int) -> bool:
        existing = self.db.scalars(
            select(MarketMapCandidateOverride).where(
                MarketMapCandidateOverride.market_map_id == map_id,
                MarketMapCandidateOverride.candidate_id == candidate_id,
            )
        ).first()
        if existing is None:
            return False
        self.db.delete(existing)
        self.db.commit()
        return True

    def list_overrides(self, map_id: int) -> list[MarketMapCandidateOverride]:
        return list(
            self.db.scalars(
                select(MarketMapCandidateOverride).where(
                    MarketMapCandidateOverride.market_map_id == map_id
                )
            ).all()
        )

    # --- Generación IA + análisis ----------------------------------------

    def generate_map_content(
        self,
        map_id: int,
        *,
        overwrite_ai_suggested: bool = True,
        overwrite_manual: bool = False,
    ) -> TalentMarketMap:
        """Genera contenido del mapa con IA (o fallback determinístico).

        Reglas de preservación:
        - Entidades con ai_suggested=True: pisadas si overwrite_ai_suggested=True
        - Entidades con ai_suggested=False (creadas por el consultor): pisadas
          sólo si overwrite_manual=True
        - executive_summary: pisado si overwrite_ai_suggested=True
        """
        map_ = self.get(map_id)
        if map_ is None:
            raise ValueError("Talent Market Map no encontrado")
        mandate = self.db.get(SearchMandate, map_.search_mandate_id)
        if mandate is None:
            raise ValueError("Mandato no encontrado")

        spec: PositionSpec | None = None
        if map_.position_spec_id:
            spec = self.db.get(PositionSpec, map_.position_spec_id)
        if spec is None:
            spec = self.db.scalars(
                select(PositionSpec)
                .where(PositionSpec.search_mandate_id == map_.search_mandate_id)
                .order_by(PositionSpec.created_at.desc())
            ).first()
            if spec is not None:
                map_.position_spec_id = spec.id

        payload = generate_talent_market_map(mandate, spec)
        meta = payload.get("_meta", {})

        # Borrar entidades que vayan a ser pisadas
        for seg in self.list_segments(map_id):
            if (seg.ai_suggested and overwrite_ai_suggested) or (
                not seg.ai_suggested and overwrite_manual
            ):
                self.db.delete(seg)
        for co in self.list_companies(map_id):
            if (co.ai_suggested and overwrite_ai_suggested) or (
                not co.ai_suggested and overwrite_manual
            ):
                self.db.delete(co)
        for role in self.list_equivalent_roles(map_id):
            if (role.ai_suggested and overwrite_ai_suggested) or (
                not role.ai_suggested and overwrite_manual
            ):
                self.db.delete(role)
        self.db.flush()

        # Crear nuevos segmentos
        segments_by_name: dict[str, MarketSegment] = {}
        for idx, seg_data in enumerate(payload.get("segments", [])):
            seg = MarketSegment(
                market_map_id=map_id,
                name=seg_data["name"],
                segment_type=seg_data["segment_type"],
                description=seg_data.get("description"),
                priority=seg_data.get("priority", "medium"),
                rationale=seg_data.get("rationale"),
                sort_order=idx,
                ai_suggested=True,
            )
            self.db.add(seg)
            self.db.flush()
            segments_by_name[_norm(seg.name)] = seg

        # También indexar segmentos manuales preexistentes para que el LLM
        # pueda referenciarlos por nombre
        for seg in self.list_segments(map_id):
            segments_by_name.setdefault(_norm(seg.name), seg)

        for co_data in payload.get("companies", []):
            seg_ref = segments_by_name.get(_norm(co_data.get("segment_name")))
            self.db.add(
                TargetCompany(
                    market_map_id=map_id,
                    segment_id=seg_ref.id if seg_ref else None,
                    name=co_data["name"],
                    industry=co_data.get("industry"),
                    priority=co_data.get("priority", "medium"),
                    rationale=co_data.get("rationale"),
                    ai_suggested=True,
                )
            )

        for role_data in payload.get("equivalent_roles", []):
            self.db.add(
                EquivalentRole(
                    market_map_id=map_id,
                    title=role_data["title"],
                    seniority=role_data.get("seniority"),
                    closeness=role_data.get("closeness", "medium"),
                    priority=role_data.get("priority", "medium"),
                    industries=list(role_data.get("industries") or []),
                    rationale=role_data.get("rationale"),
                    ai_suggested=True,
                )
            )

        # Actualizar mapa
        if overwrite_ai_suggested or not map_.executive_summary:
            map_.executive_summary = payload.get("executive_summary")
        map_.market_assessment = payload.get("market_assessment", "moderate")
        map_.generated_by_model = meta.get("generated_by_model")
        map_.prompt_version = meta.get("prompt_version")
        map_.generated_at = datetime.now(timezone.utc)
        if map_.status in ("draft", "generated"):
            map_.status = "generated"
        else:
            map_.status = "updated"
        self.db.add(map_)
        self.db.commit()
        self.db.refresh(map_)
        return map_

    def recompute_gaps(self, map_id: int) -> list[MarketGap]:
        map_ = self.get(map_id)
        if map_ is None:
            raise ValueError("Talent Market Map no encontrado")
        _items, _candidates, evaluations_map, _profiles = self.candidates_for_mandate(
            map_.search_mandate_id
        )
        evaluations = list(evaluations_map.values())
        gaps_data = detect_gaps(evaluations)
        self.replace_gaps(map_id, gaps_data)
        return self.list_gaps(map_id)

    def regenerate_recommendations(
        self, map_id: int
    ) -> list[RecalibrationRecommendation]:
        map_ = self.get(map_id)
        if map_ is None:
            raise ValueError("Talent Market Map no encontrado")
        coverage = self.compute_coverage(map_.search_mandate_id, map_id)
        pipeline_items, _candidates, evaluations_map, _profiles = (
            self.candidates_for_mandate(map_.search_mandate_id)
        )
        companies = self.list_companies(map_id)
        gaps_data = [
            {
                "title": g.title,
                "frequency": g.frequency,
                "total_evaluated": g.total_evaluated,
                "impact": g.impact,
                "recommendation": g.recommendation,
            }
            for g in self.list_gaps(map_id)
        ]
        recs = generate_rule_recommendations(
            coverage_pct=coverage["coverage_pct"],
            target_companies=companies,
            pipeline_items=pipeline_items,
            evaluations_map=evaluations_map,
            gaps_data=gaps_data,
            shortlisted_count=coverage["shortlisted"],
        )
        self.replace_suggested_recommendations(map_id, recs)
        return self.list_recommendations(map_id)

    # --- Cobertura (calculada en tiempo real) ----------------------------

    def candidates_for_mandate(
        self, mandate_id: int
    ) -> tuple[
        list[CandidatePipelineItem],
        dict[int, Candidate],
        dict[int, CandidateEvaluation],
        dict[int, CandidateProfile],
    ]:
        """Devuelve pipeline items + caches de candidates/evaluations/profiles."""
        pipeline_items = list(
            self.db.scalars(
                select(CandidatePipelineItem).where(
                    CandidatePipelineItem.mandate_id == mandate_id
                )
            ).all()
        )
        candidate_ids = {it.candidate_id for it in pipeline_items}
        eval_ids = {it.evaluation_id for it in pipeline_items if it.evaluation_id}

        candidates_map: dict[int, Candidate] = {}
        for cid in candidate_ids:
            c = self.db.get(Candidate, cid)
            if c is not None:
                candidates_map[cid] = c

        evaluations_map: dict[int, CandidateEvaluation] = {}
        for eid in eval_ids:
            e = self.db.get(CandidateEvaluation, eid)
            if e is not None:
                evaluations_map[eid] = e

        profiles_map: dict[int, CandidateProfile] = {}
        for cid in candidate_ids:
            profile = self.db.scalars(
                select(CandidateProfile)
                .where(CandidateProfile.candidate_id == cid)
                .order_by(CandidateProfile.created_at.desc())
            ).first()
            if profile is not None:
                profiles_map[cid] = profile

        return pipeline_items, candidates_map, evaluations_map, profiles_map

    def compute_coverage(self, mandate_id: int, map_id: int) -> dict[str, Any]:
        """Calcula KPIs de cobertura del mandato vs el mapa."""
        pipeline_items, candidates_map, evaluations_map, profiles_map = (
            self.candidates_for_mandate(mandate_id)
        )

        identified = len(pipeline_items)
        loaded = sum(
            1 for it in pipeline_items if it.candidate_id in candidates_map
        )
        evaluated_items = [
            it for it in pipeline_items if it.evaluation_id in evaluations_map
        ]
        evaluated = len(evaluated_items)
        high_fit = sum(
            1
            for it in evaluated_items
            if evaluations_map[it.evaluation_id].total_score >= 70
        )
        medium_fit = sum(
            1
            for it in evaluated_items
            if 55 <= evaluations_map[it.evaluation_id].total_score < 70
        )
        low_fit = sum(
            1
            for it in evaluated_items
            if evaluations_map[it.evaluation_id].total_score < 55
        )
        discarded = sum(1 for it in pipeline_items if it.stage == "discarded")

        # Shortlist: candidatos en al menos un ClientShortlist del mandato
        shortlist_candidate_ids = set(
            self.db.scalars(
                select(ClientShortlistItem.candidate_id)
                .join(ClientShortlist, ClientShortlist.id == ClientShortlistItem.shortlist_id)
                .where(ClientShortlist.mandate_id == mandate_id)
            ).all()
        )
        shortlisted = sum(
            1 for it in pipeline_items if it.candidate_id in shortlist_candidate_ids
        )

        companies = self.list_companies(map_id)
        target_companies_total = len(companies)
        target_companies_reviewed = sum(
            1
            for c in companies
            if c.coverage_status
            in (
                "covered",
                "partially_covered",
                "no_relevant_candidates",
                "discarded",
            )
        )
        target_companies_pending = target_companies_total - target_companies_reviewed

        # Industrias cubiertas: industrias únicas presentes en profiles
        industries_set: set[str] = set()
        for profile in profiles_map.values():
            for ind in profile.industries or []:
                if isinstance(ind, str) and ind.strip():
                    industries_set.add(ind.strip())

        # Cobertura general: weighted simple
        # - peso 1.5 evaluación, 1 carga, 1 cobertura empresas
        max_score = (identified * 1.5) + target_companies_total * 1 + 1
        actual_score = (
            evaluated * 1.5
            + target_companies_reviewed * 1
            + (1 if shortlisted > 0 else 0)
        )
        coverage_pct = int(min(100, (actual_score / max_score) * 100)) if max_score > 0 else 0

        return {
            "candidates_identified": identified,
            "candidates_loaded": loaded,
            "candidates_evaluated": evaluated,
            "high_fit": high_fit,
            "medium_fit": medium_fit,
            "low_fit": low_fit,
            "discarded": discarded,
            "shortlisted": shortlisted,
            "target_companies_total": target_companies_total,
            "target_companies_reviewed": target_companies_reviewed,
            "target_companies_pending": target_companies_pending,
            "industries_covered": len(industries_set),
            "coverage_pct": coverage_pct,
        }

    # --- Conteos por entidad (derivados) --------------------------------

    def candidate_counts_by_company(
        self, map_id: int, mandate_id: int
    ) -> dict[int, dict[str, int]]:
        """Para cada target_company, cuenta candidatos auto-detectados + overrides.

        Auto-detectado: candidate.current_company casefold == company.name casefold.
        Override: vía MarketMapCandidateOverride.target_company_id.
        """
        companies = self.list_companies(map_id)
        if not companies:
            return {}
        pipeline_items, candidates_map, evaluations_map, _profiles = (
            self.candidates_for_mandate(mandate_id)
        )
        overrides = self.list_overrides(map_id)
        override_by_cand = {
            o.candidate_id: o for o in overrides if o.target_company_id is not None
        }

        result: dict[int, dict[str, int]] = {}
        for co in companies:
            co_norm = _norm(co.name)
            identified = 0
            evaluated = 0
            high_fit = 0
            for it in pipeline_items:
                cand = candidates_map.get(it.candidate_id)
                if cand is None:
                    continue
                override = override_by_cand.get(it.candidate_id)
                match = False
                if override and override.target_company_id == co.id:
                    match = True
                elif cand.current_company and _norm(cand.current_company) == co_norm:
                    match = True
                if not match:
                    continue
                identified += 1
                ev = evaluations_map.get(it.evaluation_id) if it.evaluation_id else None
                if ev is not None:
                    evaluated += 1
                    if ev.total_score >= 70:
                        high_fit += 1
            result[co.id] = {
                "identified": identified,
                "evaluated": evaluated,
                "high_fit": high_fit,
            }
        return result

    def candidate_counts_by_segment(
        self, map_id: int, mandate_id: int
    ) -> dict[int, int]:
        """Cuenta candidatos por segmento (vía overrides + via companies del segmento)."""
        segments = self.list_segments(map_id)
        if not segments:
            return {}
        companies = self.list_companies(map_id)
        comp_by_segment: dict[int, list[int]] = {s.id: [] for s in segments}
        for co in companies:
            if co.segment_id and co.segment_id in comp_by_segment:
                comp_by_segment[co.segment_id].append(co.id)

        per_company = self.candidate_counts_by_company(map_id, mandate_id)
        overrides = self.list_overrides(map_id)
        override_by_segment: dict[int, set[int]] = {s.id: set() for s in segments}
        for o in overrides:
            if o.segment_id and o.segment_id in override_by_segment:
                override_by_segment[o.segment_id].add(o.candidate_id)

        result: dict[int, int] = {}
        for s in segments:
            # Suma candidatos identificados en empresas del segmento (sin doble contar overrides)
            from_companies = sum(
                per_company.get(co_id, {}).get("identified", 0)
                for co_id in comp_by_segment.get(s.id, [])
            )
            from_overrides = len(override_by_segment.get(s.id, set()))
            result[s.id] = from_companies + from_overrides
        return result

    def candidate_counts_by_equivalent_role(
        self, map_id: int, mandate_id: int
    ) -> dict[int, int]:
        """Cuenta candidatos asignados manualmente a cada cargo equivalente."""
        roles = self.list_equivalent_roles(map_id)
        if not roles:
            return {}
        overrides = self.list_overrides(map_id)
        counter = Counter(o.equivalent_role_id for o in overrides if o.equivalent_role_id)
        return {r.id: counter.get(r.id, 0) for r in roles}
