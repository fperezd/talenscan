"""Servicio de la Bóveda de Talento (Talent Vault).

Responsabilidades:
- CRUD del Perfil Maestro de Talento, con versionamiento ante cambios críticos.
- Métricas de la bóveda.
- Notas, tags, documentos, evaluaciones e historial de procesos.
- Detección determinística de duplicados (email/linkedin/teléfono + nombre+empresa).

No rompe módulos existentes: sólo lee/escribe entidades nuevas y referencia
las existentes (candidates, candidate_evaluations, etc.) por id.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.talent_profile import (
    TalentDocument,
    TalentEvaluation,
    TalentNote,
    TalentProcessHistory,
    TalentProfile,
    TalentProfileTag,
    TalentProfileVersion,
    TalentTag,
)


# Campos cuyo cambio dispara un snapshot de versión.
_VERSIONED_FIELDS = (
    "full_name",
    "primary_email",
    "linkedin_url",
    "current_position",
    "current_company",
    "summary",
    "skills",
    "industries",
    "status",
    "availability_status",
)


def _norm(value: str | None) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", text)
    no_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return no_accents.casefold()


def _norm_phone(value: str | None) -> str:
    return re.sub(r"\D", "", value or "")[-9:] if value else ""


class TalentProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Lectura ---------------------------------------------------------

    def get(self, talent_id: int) -> TalentProfile | None:
        profile = self.db.get(TalentProfile, talent_id)
        if profile is None or profile.is_deleted:
            return None
        return profile

    def list_tags_for(self, talent_id: int) -> list[TalentTag]:
        return list(
            self.db.scalars(
                select(TalentTag)
                .join(TalentProfileTag, TalentProfileTag.tag_id == TalentTag.id)
                .where(TalentProfileTag.talent_profile_id == talent_id)
                .order_by(TalentTag.name.asc())
            ).all()
        )

    def list_documents(self, talent_id: int) -> list[TalentDocument]:
        return list(
            self.db.scalars(
                select(TalentDocument)
                .where(TalentDocument.talent_profile_id == talent_id)
                .order_by(TalentDocument.created_at.desc(), TalentDocument.id.desc())
            ).all()
        )

    def list_evaluations(self, talent_id: int) -> list[TalentEvaluation]:
        return list(
            self.db.scalars(
                select(TalentEvaluation)
                .where(TalentEvaluation.talent_profile_id == talent_id)
                .order_by(TalentEvaluation.created_at.desc(), TalentEvaluation.id.desc())
            ).all()
        )

    def list_process_history(self, talent_id: int) -> list[TalentProcessHistory]:
        return list(
            self.db.scalars(
                select(TalentProcessHistory)
                .where(TalentProcessHistory.talent_profile_id == talent_id)
                .order_by(TalentProcessHistory.updated_at.desc())
            ).all()
        )

    def list_notes(self, talent_id: int) -> list[TalentNote]:
        return list(
            self.db.scalars(
                select(TalentNote)
                .where(TalentNote.talent_profile_id == talent_id)
                .order_by(TalentNote.created_at.desc(), TalentNote.id.desc())
            ).all()
        )

    def list_versions(self, talent_id: int) -> list[TalentProfileVersion]:
        return list(
            self.db.scalars(
                select(TalentProfileVersion)
                .where(TalentProfileVersion.talent_profile_id == talent_id)
                .order_by(TalentProfileVersion.version_number.desc())
            ).all()
        )

    def latest_score(self, talent_id: int) -> int | None:
        ev = self.db.scalars(
            select(TalentEvaluation)
            .where(
                TalentEvaluation.talent_profile_id == talent_id,
                TalentEvaluation.total_score.is_not(None),
            )
            .order_by(TalentEvaluation.created_at.desc())
        ).first()
        return ev.total_score if ev else None

    # --- Lista + filtros + métricas --------------------------------------

    def list_profiles(
        self,
        *,
        search: str | None = None,
        status: str | None = None,
        availability: str | None = None,
        industry: str | None = None,
        seniority: str | None = None,
        skill: str | None = None,
        min_score: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TalentProfile], int]:
        query = select(TalentProfile).where(TalentProfile.is_deleted.is_(False))

        if search:
            like = f"%{search.strip()}%"
            query = query.where(
                or_(
                    TalentProfile.full_name.ilike(like),
                    TalentProfile.current_company.ilike(like),
                    TalentProfile.current_position.ilike(like),
                    TalentProfile.primary_email.ilike(like),
                )
            )
        if status:
            query = query.where(TalentProfile.status == status)
        if availability:
            query = query.where(TalentProfile.availability_status == availability)
        if seniority:
            query = query.where(TalentProfile.inferred_seniority == seniority)

        all_rows = list(self.db.scalars(query.order_by(TalentProfile.updated_at.desc())).all())

        # Filtros sobre JSON (industries/skills) y score: en Python para
        # portabilidad SQLite/Postgres en el MVP.
        def has_token(items: Any, needle: str) -> bool:
            n = _norm(needle)
            return any(_norm(str(x)) == n or n in _norm(str(x)) for x in (items or []))

        if industry:
            all_rows = [p for p in all_rows if has_token(p.industries, industry)]
        if skill:
            all_rows = [p for p in all_rows if has_token(p.skills, skill)]
        if min_score is not None:
            all_rows = [
                p for p in all_rows if (self.latest_score(p.id) or 0) >= min_score
            ]

        total = len(all_rows)
        start = max(0, (page - 1) * page_size)
        return all_rows[start : start + page_size], total

    def metrics(self) -> dict[str, Any]:
        profiles = list(
            self.db.scalars(
                select(TalentProfile).where(TalentProfile.is_deleted.is_(False))
            ).all()
        )
        total = len(profiles)
        evaluated = sum(1 for p in profiles if p.last_evaluated_at is not None)
        in_reserve = sum(1 for p in profiles if p.status == "passive")
        available = sum(
            1 for p in profiles if p.availability_status in ("available", "open_to_offers")
        )
        scores = [s for s in (self.latest_score(p.id) for p in profiles) if s is not None]
        average_score = int(sum(scores) / len(scores)) if scores else None
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        updated_last_30 = sum(
            1
            for p in profiles
            if p.updated_at and _aware(p.updated_at) >= cutoff
        )
        return {
            "total": total,
            "evaluated": evaluated,
            "in_reserve": in_reserve,
            "available": available,
            "average_score": average_score,
            "updated_last_30_days": updated_last_30,
        }

    # --- Crear / actualizar / borrar -------------------------------------

    def create(self, data: dict[str, Any]) -> TalentProfile:
        profile = TalentProfile(**data)
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        self._snapshot(profile, change_reason="Creación del perfil", source="manual")
        return profile

    def update(
        self, talent_id: int, patch: dict[str, Any], *, change_reason: str | None = None
    ) -> TalentProfile | None:
        profile = self.get(talent_id)
        if profile is None:
            return None
        critical_changed = False
        for key, value in patch.items():
            if value is None:
                continue
            if hasattr(profile, key) and getattr(profile, key) != value:
                if key in _VERSIONED_FIELDS:
                    critical_changed = True
                setattr(profile, key, value)
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        if critical_changed:
            self._snapshot(
                profile,
                change_reason=change_reason or "Actualización de campos clave",
                source="manual",
            )
        return profile

    def soft_delete(self, talent_id: int) -> bool:
        profile = self.get(talent_id)
        if profile is None:
            return False
        profile.is_deleted = True
        profile.status = "archived"
        self.db.add(profile)
        self.db.commit()
        return True

    def _snapshot(
        self, profile: TalentProfile, *, change_reason: str, source: str
    ) -> None:
        last = self.db.scalars(
            select(TalentProfileVersion)
            .where(TalentProfileVersion.talent_profile_id == profile.id)
            .order_by(TalentProfileVersion.version_number.desc())
        ).first()
        next_number = (last.version_number + 1) if last else 1
        snapshot = {
            "full_name": profile.full_name,
            "primary_email": profile.primary_email,
            "current_position": profile.current_position,
            "current_company": profile.current_company,
            "summary": profile.summary,
            "skills": list(profile.skills or []),
            "industries": list(profile.industries or []),
            "status": profile.status,
            "availability_status": profile.availability_status,
        }
        self.db.add(
            TalentProfileVersion(
                talent_profile_id=profile.id,
                version_number=next_number,
                snapshot_json=snapshot,
                change_reason=change_reason,
                source=source,
            )
        )
        self.db.commit()

    # --- Notas -----------------------------------------------------------

    def add_note(self, talent_id: int, data: dict[str, Any]) -> TalentNote | None:
        if self.get(talent_id) is None:
            return None
        note = TalentNote(talent_profile_id=talent_id, **data)
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note

    def update_note(
        self, talent_id: int, note_id: int, patch: dict[str, Any]
    ) -> TalentNote | None:
        note = self.db.get(TalentNote, note_id)
        if note is None or note.talent_profile_id != talent_id:
            return None
        for key, value in patch.items():
            if value is not None and hasattr(note, key):
                setattr(note, key, value)
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note

    def delete_note(self, talent_id: int, note_id: int) -> bool:
        note = self.db.get(TalentNote, note_id)
        if note is None or note.talent_profile_id != talent_id:
            return False
        self.db.delete(note)
        self.db.commit()
        return True

    # --- Tags ------------------------------------------------------------

    def list_tag_catalog(self) -> list[TalentTag]:
        return list(self.db.scalars(select(TalentTag).order_by(TalentTag.name.asc())).all())

    def assign_tag(
        self, talent_id: int, name: str, category: str | None = None
    ) -> TalentTag | None:
        if self.get(talent_id) is None:
            return None
        norm = name.strip()
        tag = self.db.scalars(select(TalentTag).where(TalentTag.name == norm)).first()
        if tag is None:
            tag = TalentTag(name=norm, category=category)
            self.db.add(tag)
            self.db.flush()
        existing = self.db.scalars(
            select(TalentProfileTag).where(
                TalentProfileTag.talent_profile_id == talent_id,
                TalentProfileTag.tag_id == tag.id,
            )
        ).first()
        if existing is None:
            self.db.add(TalentProfileTag(talent_profile_id=talent_id, tag_id=tag.id))
        self._refresh_tags_snapshot(talent_id)
        self.db.commit()
        return tag

    def remove_tag(self, talent_id: int, tag_id: int) -> bool:
        link = self.db.scalars(
            select(TalentProfileTag).where(
                TalentProfileTag.talent_profile_id == talent_id,
                TalentProfileTag.tag_id == tag_id,
            )
        ).first()
        if link is None:
            return False
        self.db.delete(link)
        self._refresh_tags_snapshot(talent_id)
        self.db.commit()
        return True

    def _refresh_tags_snapshot(self, talent_id: int) -> None:
        profile = self.db.get(TalentProfile, talent_id)
        if profile is not None:
            self.db.flush()
            profile.tags_snapshot = [t.name for t in self.list_tags_for(talent_id)]
            self.db.add(profile)

    # --- Documentos / evaluaciones (escritura básica) --------------------

    def add_document(self, talent_id: int, data: dict[str, Any]) -> TalentDocument | None:
        if self.get(talent_id) is None:
            return None
        doc = TalentDocument(talent_profile_id=talent_id, **data)
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def record_evaluation(self, talent_id: int, data: dict[str, Any]) -> TalentEvaluation:
        ev = TalentEvaluation(talent_profile_id=talent_id, **data)
        self.db.add(ev)
        profile = self.db.get(TalentProfile, talent_id)
        if profile is not None:
            profile.last_evaluated_at = datetime.now(timezone.utc)
            self.db.add(profile)
        self.db.commit()
        self.db.refresh(ev)
        return ev

    # --- Detección de duplicados -----------------------------------------

    def detect_duplicates(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        email = _norm(payload.get("primary_email"))
        linkedin = _norm(payload.get("linkedin_url"))
        phone = _norm_phone(payload.get("primary_phone"))
        name = _norm(payload.get("full_name"))
        company = _norm(payload.get("current_company"))

        candidates = list(
            self.db.scalars(
                select(TalentProfile).where(TalentProfile.is_deleted.is_(False))
            ).all()
        )
        matches: list[dict[str, Any]] = []
        for p in candidates:
            reasons: list[str] = []
            score = 0.0
            if email and _norm(p.primary_email) == email:
                reasons.append("email_exact")
                score = max(score, 0.97)
            if linkedin and _norm(p.linkedin_url) == linkedin:
                reasons.append("linkedin_exact")
                score = max(score, 0.95)
            if phone and _norm_phone(p.primary_phone) == phone:
                reasons.append("phone_exact")
                score = max(score, 0.9)
            if name and _norm(p.full_name) == name:
                if company and _norm(p.current_company) == company:
                    reasons.append("name_and_company")
                    score = max(score, 0.85)
                else:
                    reasons.append("name_exact")
                    score = max(score, 0.6)
            if reasons:
                matches.append(
                    {
                        "talent_profile_id": p.id,
                        "match_score": round(score, 2),
                        "match_reasons": reasons,
                        "full_name": p.full_name,
                        "current_company": p.current_company,
                        "current_position": p.current_position,
                    }
                )
        matches.sort(key=lambda m: m["match_score"], reverse=True)
        return matches


def _aware(dt: datetime) -> datetime:
    """Normaliza a tz-aware UTC (SQLite devuelve naive)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
