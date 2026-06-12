"""Servicio del Decision Room (alias técnico: ClientShortlist).

Responsabilidades:
- Crear y configurar Decision Rooms con token URL-safe único.
- Gate de acceso por código de 6 dígitos (hash en DB, código en claro solo se devuelve una vez).
- Validación de código → emite session token HMAC-firmado, sin estado en DB.
- Regenerar acceso (invalida token y código anteriores).
- Editar overrides del consultor (resumen, why_fits, riesgos, evidencia, etc).
- Reordenar y pinear candidatos.
- Sanitizar vista pública respetando toggles de visibilidad.
- Registrar feedback del cliente y propagarlo al pipeline (futuro).
- Registrar eventos en timeline interno.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.candidate import Candidate
from app.models.candidate_evaluation import CandidateEvaluation
from app.models.candidate_profile import CandidateProfile
from app.models.client_shortlist import (
    CLIENT_FEEDBACK_STATUSES,
    ClientShortlist,
    ClientShortlistItem,
    DecisionRoomEvent,
)
from app.models.search_mandate import SearchMandate


# --- Helpers de token / código ---------------------------------------------


def _generate_token() -> str:
    """Token URL-safe de ~32 chars, no secuencial, suficientemente impredecible."""
    return secrets.token_urlsafe(24)


def _generate_access_code() -> str:
    """6 dígitos aleatorios uniformes (spec §6)."""
    return f"{secrets.randbelow(1_000_000):06d}"


def _hash_code(code: str, salt: str) -> str:
    """SHA-256 con salt (el `public_token` del room actúa como salt natural)."""
    return hashlib.sha256(f"{salt}:{code}".encode("utf-8")).hexdigest()


def _verify_code(code: str, code_hash: str, salt: str) -> bool:
    return hmac.compare_digest(_hash_code(code, salt), code_hash)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


# --- Session token (HMAC firmado, sin estado) ------------------------------


def _sign_session(payload: dict[str, Any]) -> str:
    body = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).rstrip(b"=")
    signature = hmac.new(
        settings.decision_room_secret.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()
    return f"{body.decode('ascii')}.{signature}"


def _verify_session(token: str | None) -> dict[str, Any] | None:
    if not token or "." not in token:
        return None
    body, signature = token.rsplit(".", 1)
    expected = hmac.new(
        settings.decision_room_secret.encode("utf-8"),
        body.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return None
    try:
        padded = body + "=" * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
    except (ValueError, json.JSONDecodeError):
        return None
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(_now().timestamp()):
        return None
    return payload


def issue_client_session(shortlist_id: int, ttl_seconds: int | None = None) -> tuple[str, datetime]:
    ttl = ttl_seconds or settings.decision_room_session_ttl_seconds
    expires_at = _now() + timedelta(seconds=ttl)
    payload = {
        "sl": shortlist_id,
        "exp": int(expires_at.timestamp()),
        "n": secrets.token_urlsafe(8),
    }
    return _sign_session(payload), expires_at


def verify_client_session(token: str | None, shortlist_id: int) -> bool:
    payload = _verify_session(token)
    return bool(payload and payload.get("sl") == shortlist_id)


# --- Sanitizadores de vista pública (lenguaje cliente) ---------------------


def _evaluation_ai(evaluation: CandidateEvaluation | None) -> dict[str, Any]:
    if evaluation is None or not isinstance(evaluation.evaluation_json, dict):
        return {}
    return evaluation.evaluation_json.get("ai_assessment", {}) or {}


def _sanitized_strengths(ai: dict[str, Any]) -> list[str]:
    detailed = ai.get("strengths_detailed") or []
    result: list[str] = []
    for item in detailed[:6]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        detail = str(item.get("detail") or "").strip()
        if title and detail:
            result.append(f"{title} — {detail}")
        elif title:
            result.append(title)
    return result


def _sanitized_areas(ai: dict[str, Any]) -> list[str]:
    gaps = ai.get("critical_gaps_detailed") or []
    result: list[str] = []
    for item in gaps[:5]:
        if not isinstance(item, dict):
            continue
        req = str(item.get("requirement") or "").strip()
        if req:
            result.append(f"Profundizar en entrevista: {req}")
    return result


def _public_experience(profile: CandidateProfile | None) -> list[dict[str, Any]]:
    """Convierte profile.roles a una lista limpia para el cliente.

    El parser a veces produce title/company desordenados (texto largo en
    title que continúa en company). Recortamos y filtramos.
    """
    if profile is None:
        return []
    roles = profile.roles or []
    cleaned: list[dict[str, Any]] = []
    for role in roles[:8]:
        if not isinstance(role, dict):
            continue
        title = str(role.get("title") or "").strip()
        company = str(role.get("company") or "").strip()
        # Cortar fragmentos absurdamente largos del parser para no romper UI
        title_short = title[:140] + ("…" if len(title) > 140 else "")
        company_short = company[:140] + ("…" if len(company) > 140 else "")
        responsibilities = [
            str(r).strip() for r in (role.get("responsibilities") or [])[:5] if str(r).strip()
        ]
        achievements = [
            str(a).strip() for a in (role.get("achievements") or [])[:5] if str(a).strip()
        ]
        tools = [
            str(t).strip()
            for t in (role.get("tools_or_systems") or [])[:8]
            if str(t).strip()
        ]
        cleaned.append(
            {
                "title": title_short,
                "company": company_short,
                "start_date": str(role.get("start_date") or "").strip() or None,
                "end_date": str(role.get("end_date") or "").strip() or None,
                "duration_years": role.get("duration_years") or None,
                "responsibilities": responsibilities,
                "achievements": achievements,
                "tools_or_systems": tools,
            }
        )
    return cleaned


def _public_dimension_scores(
    evaluation: CandidateEvaluation | None,
) -> list[dict[str, Any]]:
    if evaluation is None:
        return []
    result: list[dict[str, Any]] = []
    for ds in evaluation.dimension_scores or []:
        if not isinstance(ds, dict):
            continue
        result.append(
            {
                "dimension": str(ds.get("dimension") or "").strip(),
                "score": ds.get("score"),
                "max_score": ds.get("max_score"),
                "status": str(ds.get("status") or "").strip() or None,
                "evidence_level": str(ds.get("evidence_level") or "").strip() or None,
                "rationale": str(ds.get("rationale") or "").strip() or None,
            }
        )
    return result


def _public_achievements(profile: CandidateProfile | None) -> list[str]:
    """Achievements del profile, truncados para no inundar la UI."""
    if profile is None:
        return []
    out: list[str] = []
    for item in (profile.achievements or [])[:5]:
        text = str(item or "").strip()
        if not text:
            continue
        # Cortamos textos kilométricos del parser
        if len(text) > 400:
            text = text[:400] + "…"
        out.append(text)
    return out


def _professional_summary(
    candidate: Candidate, profile: CandidateProfile | None, ai: dict[str, Any]
) -> str:
    thesis = str(ai.get("talent_thesis") or "").strip()
    if thesis:
        return thesis
    differentiation = str(ai.get("differentiation") or "").strip()
    if differentiation:
        return differentiation
    pieces: list[str] = []
    if candidate.current_position:
        pieces.append(candidate.current_position)
    if candidate.current_company:
        pieces.append(f"en {candidate.current_company}")
    if profile and profile.total_years_experience:
        pieces.append(f"con {profile.total_years_experience} años de experiencia")
    if profile and profile.inferred_seniority:
        pieces.append(f"de nivel {profile.inferred_seniority}")
    return " ".join(pieces) or "Candidato pre-seleccionado por TalentScan."


def _headline(candidate: Candidate, profile: CandidateProfile | None) -> str:
    role = candidate.current_position or "Profesional"
    company = candidate.current_company
    if company:
        return f"{role} · {company}"
    if profile and profile.inferred_seniority:
        return f"{role} · {profile.inferred_seniority}"
    return role


def _hint_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    local, _, domain = email.partition("@")
    if len(local) <= 1:
        return f"*@{domain}"
    return f"{local[0]}***@{domain}"


# --- Service ---------------------------------------------------------------


class ClientShortlistService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Admin: CRUD del room -------------------------------------------------

    def create(
        self,
        *,
        mandate_id: int,
        title: str,
        message_to_client: str,
        show_scores: bool,
        evaluation_ids: list[int],
        expires_at: datetime | None = None,
        intro_message: str | None = None,
        show_availability: bool = False,
        show_salary: bool = False,
        show_risks: bool = False,
        show_comparison: bool = True,
        allow_comments: bool = True,
        allow_rating: bool = False,
        allow_report_download: bool = False,
        access_code_required: bool = False,
        client_contact_name: str | None = None,
        client_contact_email: str | None = None,
        client_contact_company: str | None = None,
    ) -> ClientShortlist:
        mandate = self.db.get(SearchMandate, mandate_id)
        if mandate is None:
            raise ValueError("Mandato no encontrado")
        if not evaluation_ids:
            raise ValueError("Debes seleccionar al menos un candidato.")

        shortlist = ClientShortlist(
            mandate_id=mandate_id,
            public_token=_generate_token(),
            title=title or "Shortlist TalentScan",
            message_to_client=message_to_client or "",
            intro_message=intro_message,
            show_scores=show_scores,
            show_availability=show_availability,
            show_salary=show_salary,
            show_risks=show_risks,
            show_comparison=show_comparison,
            allow_comments=allow_comments,
            allow_rating=allow_rating,
            allow_report_download=allow_report_download,
            access_code_required=access_code_required,
            client_contact_name=client_contact_name,
            client_contact_email=client_contact_email,
            client_contact_company=client_contact_company,
            expires_at=expires_at,
            status="draft",
        )
        self.db.add(shortlist)
        self.db.flush()

        evaluations: list[CandidateEvaluation] = []
        for eval_id in evaluation_ids:
            evaluation = self.db.get(CandidateEvaluation, eval_id)
            if evaluation is None:
                continue
            evaluations.append(evaluation)
        evaluations.sort(key=lambda e: e.total_score, reverse=True)

        for index, evaluation in enumerate(evaluations):
            item = ClientShortlistItem(
                shortlist_id=shortlist.id,
                evaluation_id=evaluation.id,
                candidate_id=evaluation.candidate_id,
                order_index=index,
            )
            self.db.add(item)

        # Si ya viene con candidatos, pasa de draft → ready_to_share.
        if evaluations:
            shortlist.status = "ready_to_share"

        self.db.flush()
        self._record_event(
            shortlist_id=shortlist.id,
            event_type="room_created",
            event_label="Decision Room creado",
            actor_type="consultant",
            metadata={"candidates": len(evaluations)},
        )
        self.db.commit()
        self.db.refresh(shortlist)
        return shortlist

    def get(self, shortlist_id: int) -> ClientShortlist | None:
        return self.db.get(ClientShortlist, shortlist_id)

    def get_by_token(self, token: str) -> ClientShortlist | None:
        return self.db.scalars(
            select(ClientShortlist).where(ClientShortlist.public_token == token)
        ).first()

    def list_by_mandate(self, mandate_id: int) -> list[ClientShortlist]:
        return list(
            self.db.scalars(
                select(ClientShortlist)
                .where(ClientShortlist.mandate_id == mandate_id)
                .order_by(ClientShortlist.created_at.desc())
            ).all()
        )

    def list_all(self) -> list[ClientShortlist]:
        return list(
            self.db.scalars(
                select(ClientShortlist).order_by(ClientShortlist.created_at.desc())
            ).all()
        )

    def items_for(self, shortlist_id: int) -> list[ClientShortlistItem]:
        return list(
            self.db.scalars(
                select(ClientShortlistItem)
                .where(ClientShortlistItem.shortlist_id == shortlist_id)
                .order_by(
                    ClientShortlistItem.is_pinned.desc(),
                    ClientShortlistItem.order_index.asc(),
                    ClientShortlistItem.id.asc(),
                )
            ).all()
        )

    def revoke(self, shortlist_id: int) -> ClientShortlist | None:
        shortlist = self.get(shortlist_id)
        if shortlist is None:
            return None
        shortlist.revoked = True
        self.db.add(shortlist)
        self._record_event(
            shortlist_id=shortlist.id,
            event_type="room_closed",
            event_label="Decision Room revocado",
            actor_type="consultant",
        )
        self.db.commit()
        self.db.refresh(shortlist)
        return shortlist

    def delete(self, shortlist_id: int) -> bool:
        shortlist = self.get(shortlist_id)
        if shortlist is None:
            return False
        # Borra items primero (eventos caen por ON DELETE CASCADE)
        for item in self.items_for(shortlist_id):
            self.db.delete(item)
        self.db.flush()
        self.db.delete(shortlist)
        self.db.commit()
        return True

    # --- Admin: configuración del room ---------------------------------------

    def update_config(self, shortlist_id: int, patch: dict[str, Any]) -> ClientShortlist | None:
        shortlist = self.get(shortlist_id)
        if shortlist is None:
            return None
        updated_fields: list[str] = []
        for field, value in patch.items():
            if value is None:
                continue
            if hasattr(shortlist, field) and getattr(shortlist, field) != value:
                setattr(shortlist, field, value)
                updated_fields.append(field)
        if updated_fields:
            self._record_event(
                shortlist_id=shortlist.id,
                event_type="room_config_updated",
                event_label="Configuración del room actualizada",
                actor_type="consultant",
                metadata={"fields": updated_fields},
            )
        self.db.add(shortlist)
        self.db.commit()
        self.db.refresh(shortlist)
        return shortlist

    def update_item_overrides(
        self, shortlist_id: int, item_id: int, patch: dict[str, Any]
    ) -> ClientShortlistItem | None:
        item = self.db.get(ClientShortlistItem, item_id)
        if item is None or item.shortlist_id != shortlist_id:
            return None
        updated_fields: list[str] = []
        for field, value in patch.items():
            if value is None:
                continue
            if hasattr(item, field) and getattr(item, field) != value:
                setattr(item, field, value)
                updated_fields.append(field)
        if updated_fields:
            self._record_event(
                shortlist_id=shortlist_id,
                item_id=item.id,
                event_type="item_overrides_updated",
                event_label="Presentación del candidato actualizada",
                actor_type="consultant",
                metadata={"fields": updated_fields},
            )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def add_item(self, shortlist_id: int, evaluation_id: int) -> ClientShortlistItem | None:
        shortlist = self.get(shortlist_id)
        if shortlist is None:
            return None
        evaluation = self.db.get(CandidateEvaluation, evaluation_id)
        if evaluation is None:
            raise ValueError("Evaluación no encontrada")
        existing = [it for it in self.items_for(shortlist_id) if it.evaluation_id == evaluation_id]
        if existing:
            # Idempotente: ya está en el room
            return existing[0]
        next_order = max(
            (it.order_index for it in self.items_for(shortlist_id)), default=-1
        ) + 1
        item = ClientShortlistItem(
            shortlist_id=shortlist_id,
            evaluation_id=evaluation_id,
            candidate_id=evaluation.candidate_id,
            order_index=next_order,
        )
        self.db.add(item)
        self.db.flush()
        self._record_event(
            shortlist_id=shortlist_id,
            item_id=item.id,
            event_type="candidate_added",
            event_label="Candidato agregado al Decision Room",
            actor_type="consultant",
            metadata={"evaluation_id": evaluation_id, "candidate_id": evaluation.candidate_id},
        )
        # Si era draft sin items, ahora pasa a ready_to_share
        if shortlist.status == "draft":
            shortlist.status = "ready_to_share"
            self.db.add(shortlist)
        self.db.commit()
        self.db.refresh(item)
        return item

    def remove_item(self, shortlist_id: int, item_id: int) -> bool:
        item = self.db.get(ClientShortlistItem, item_id)
        if item is None or item.shortlist_id != shortlist_id:
            return False
        candidate_id = item.candidate_id
        self.db.delete(item)
        self.db.flush()
        self._record_event(
            shortlist_id=shortlist_id,
            event_type="candidate_removed",
            event_label="Candidato removido del Decision Room",
            actor_type="consultant",
            metadata={"candidate_id": candidate_id, "item_id": item_id},
        )
        self.db.commit()
        return True

    def reorder_items(
        self, shortlist_id: int, ordered_item_ids: list[int]
    ) -> list[ClientShortlistItem]:
        items = {item.id: item for item in self.items_for(shortlist_id)}
        for index, item_id in enumerate(ordered_item_ids):
            item = items.get(item_id)
            if item is None:
                continue
            if item.order_index != index:
                item.order_index = index
                self.db.add(item)
        self._record_event(
            shortlist_id=shortlist_id,
            event_type="candidate_reordered",
            event_label="Orden de candidatos actualizado",
            actor_type="consultant",
            metadata={"order": ordered_item_ids},
        )
        self.db.commit()
        return self.items_for(shortlist_id)

    def pin_item(self, shortlist_id: int, item_id: int, pinned: bool) -> ClientShortlistItem | None:
        item = self.db.get(ClientShortlistItem, item_id)
        if item is None or item.shortlist_id != shortlist_id:
            return None
        item.is_pinned = pinned
        self.db.add(item)
        self._record_event(
            shortlist_id=shortlist_id,
            item_id=item.id,
            event_type="candidate_pinned" if pinned else "candidate_unpinned",
            event_label=("Candidato destacado" if pinned else "Candidato desdestacado"),
            actor_type="consultant",
        )
        self.db.commit()
        self.db.refresh(item)
        return item

    def close_room(self, shortlist_id: int) -> ClientShortlist | None:
        shortlist = self.get(shortlist_id)
        if shortlist is None:
            return None
        shortlist.status = "closed"
        shortlist.closed_at = _now()
        self.db.add(shortlist)
        self._record_event(
            shortlist_id=shortlist.id,
            event_type="room_closed",
            event_label="Decision Room cerrado",
            actor_type="consultant",
        )
        self.db.commit()
        self.db.refresh(shortlist)
        return shortlist

    def mark_invitation_sent(self, shortlist_id: int) -> ClientShortlist | None:
        shortlist = self.get(shortlist_id)
        if shortlist is None:
            return None
        shortlist.last_invitation_sent_at = _now()
        if shortlist.status in ("draft", "ready_to_share"):
            shortlist.status = "invitation_sent"
        self.db.add(shortlist)
        self._record_event(
            shortlist_id=shortlist.id,
            event_type="invitation_sent",
            event_label="Invitación enviada/copiada para el cliente",
            actor_type="consultant",
            actor_email=shortlist.client_contact_email,
        )
        self.db.commit()
        self.db.refresh(shortlist)
        return shortlist

    # --- Admin: access code ---------------------------------------------------

    def issue_access_code(
        self, shortlist_id: int, ttl_hours: int = 168
    ) -> tuple[ClientShortlist, str, datetime]:
        shortlist = self.get(shortlist_id)
        if shortlist is None:
            raise ValueError("Decision Room no encontrado")
        code = _generate_access_code()
        shortlist.access_code_hash = _hash_code(code, salt=shortlist.public_token)
        shortlist.access_code_expires_at = _now() + timedelta(hours=ttl_hours)
        shortlist.access_code_required = True
        if shortlist.status == "draft":
            shortlist.status = "ready_to_share"
        self.db.add(shortlist)
        self._record_event(
            shortlist_id=shortlist.id,
            event_type="code_generated",
            event_label="Código de validación generado",
            actor_type="consultant",
            metadata={"ttl_hours": ttl_hours},
        )
        self.db.commit()
        self.db.refresh(shortlist)
        return shortlist, code, shortlist.access_code_expires_at  # type: ignore[return-value]

    def validate_access_code(self, token: str, code: str) -> tuple[str, datetime] | None:
        shortlist = self.get_by_token(token)
        if shortlist is None or shortlist.revoked:
            return None
        if not shortlist.access_code_required or not shortlist.access_code_hash:
            # Si el room no exige código, no hay nada que validar — sesión libre.
            session, exp = issue_client_session(shortlist.id)
            return session, exp
        code_exp = _aware(shortlist.access_code_expires_at)
        if code_exp is None or code_exp < _now():
            self._record_event(
                shortlist_id=shortlist.id,
                event_type="access_expired",
                event_label="Intento de validación con código expirado",
                actor_type="client",
            )
            self.db.commit()
            return None
        if not _verify_code(code, shortlist.access_code_hash, salt=shortlist.public_token):
            self._record_event(
                shortlist_id=shortlist.id,
                event_type="code_rejected",
                event_label="Código incorrecto",
                actor_type="client",
            )
            self.db.commit()
            return None
        # OK
        self._record_event(
            shortlist_id=shortlist.id,
            event_type="code_validated",
            event_label="Código validado",
            actor_type="client",
        )
        if shortlist.viewed_at is None:
            self._record_event(
                shortlist_id=shortlist.id,
                event_type="client_entered",
                event_label="Cliente ingresó al Decision Room",
                actor_type="client",
            )
        self.db.commit()
        return issue_client_session(shortlist.id)

    def regenerate_access(
        self, shortlist_id: int, ttl_hours: int = 168
    ) -> tuple[ClientShortlist, str, str, datetime]:
        shortlist = self.get(shortlist_id)
        if shortlist is None:
            raise ValueError("Decision Room no encontrado")
        shortlist.public_token = _generate_token()
        code = _generate_access_code()
        shortlist.access_code_hash = _hash_code(code, salt=shortlist.public_token)
        shortlist.access_code_expires_at = _now() + timedelta(hours=ttl_hours)
        shortlist.access_code_required = True
        self.db.add(shortlist)
        self._record_event(
            shortlist_id=shortlist.id,
            event_type="link_regenerated",
            event_label="Link y código regenerados (anteriores invalidados)",
            actor_type="consultant",
        )
        self.db.commit()
        self.db.refresh(shortlist)
        return shortlist, shortlist.public_token, code, shortlist.access_code_expires_at  # type: ignore[return-value]

    # --- Public: vista cliente -----------------------------------------------

    def is_link_active(self, shortlist: ClientShortlist) -> bool:
        if shortlist.revoked or shortlist.status == "closed":
            return False
        exp = _aware(shortlist.expires_at)
        if exp is not None and exp < _now():
            return False
        return True

    def link_status_or_none(self, shortlist: ClientShortlist) -> str | None:
        if shortlist.revoked:
            return "revoked"
        if shortlist.status == "closed":
            return "closed"
        exp = _aware(shortlist.expires_at)
        if exp is not None and exp < _now():
            return "expired"
        return None

    def build_gate_view(self, shortlist: ClientShortlist) -> dict[str, Any]:
        mandate = self.db.get(SearchMandate, shortlist.mandate_id)
        return {
            "requires_code": True,
            "title": shortlist.title,
            "mandate": {
                "client_name": mandate.client_name if mandate else "—",
                "target_role": mandate.target_role if mandate else "—",
            },
            "expires_at": shortlist.expires_at,
            "client_contact_email_hint": _hint_email(shortlist.client_contact_email),
        }

    def build_public_view(self, shortlist: ClientShortlist) -> dict[str, Any]:
        """Vista sanitizada para el cliente, respetando todos los toggles."""
        mandate = self.db.get(SearchMandate, shortlist.mandate_id)
        items = self.items_for(shortlist.id)

        candidates_payload: list[dict[str, Any]] = []
        for item in items:
            candidate = self.db.get(Candidate, item.candidate_id)
            if candidate is None:
                continue
            evaluation = (
                self.db.get(CandidateEvaluation, item.evaluation_id)
                if item.evaluation_id
                else None
            )
            ai = _evaluation_ai(evaluation)
            profile = self.db.scalars(
                select(CandidateProfile)
                .where(CandidateProfile.candidate_id == candidate.id)
                .order_by(CandidateProfile.created_at.desc())
            ).first()

            # Overrides del consultor pisan a lo derivado de IA cuando existen.
            why_fits = item.why_fits or _sanitized_strengths(ai)
            risks = item.risks_or_validations if shortlist.show_risks else []
            # Si el room no expone riesgos, no devolverlos al cliente bajo ningún
            # nombre, ni siquiera como "áreas a validar" derivadas de la IA.
            areas = _sanitized_areas(ai) if shortlist.show_risks else []

            availability_value = (
                item.availability if shortlist.show_availability else None
            )
            salary_value = (
                item.salary_expectation
                if (shortlist.show_salary and item.salary_share_authorized)
                else None
            )

            candidates_payload.append(
                {
                    "item_id": item.id,
                    "candidate_id": candidate.id,
                    "full_name": candidate.full_name,
                    "current_position": candidate.current_position,
                    "current_company": candidate.current_company,
                    "country": candidate.country,
                    "linkedin_url": candidate.linkedin_url,
                    "total_years_experience": profile.total_years_experience if profile else None,
                    "inferred_seniority": profile.inferred_seniority if profile else None,
                    "headline": _headline(candidate, profile),
                    "professional_summary": item.consultant_summary
                    or _professional_summary(candidate, profile, ai),
                    "strengths": _sanitized_strengths(ai),
                    "transferable_skills": list(ai.get("transferable_skills") or [])[:8],
                    "career_trajectory": ai.get("career_trajectory") or {},
                    "education": list(profile.education) if profile else [],
                    "certifications": list(profile.certifications) if profile else [],
                    "languages": list(profile.languages) if profile else [],
                    "areas_to_validate": areas,
                    "why_fits": list(why_fits),
                    "risks_or_validations": list(risks),
                    "experience": _public_experience(profile),
                    "industries": list(profile.industries) if profile else [],
                    "achievements": _public_achievements(profile),
                    "tools": list(profile.tools) if profile else [],
                    "dimension_scores": (
                        _public_dimension_scores(evaluation)
                        if shortlist.show_scores
                        else []
                    ),
                    "interview_questions": (
                        list(evaluation.interview_questions or [])[:8]
                        if (evaluation and shortlist.show_risks)
                        else []
                    ),
                    "final_verdict": (
                        evaluation.final_verdict
                        if (evaluation and shortlist.show_scores)
                        else None
                    ),
                    "has_report": evaluation is not None,
                    "can_download_report": bool(
                        evaluation is not None and shortlist.allow_report_download
                    ),
                    "consultant_summary": item.consultant_summary,
                    "recommendation": item.recommendation,
                    "evidence_level": item.evidence_level,
                    "availability": availability_value,
                    "salary_expectation": salary_value,
                    "is_pinned": item.is_pinned,
                    "order_index": item.order_index,
                    "score": (
                        evaluation.total_score
                        if (evaluation and shortlist.show_scores)
                        else None
                    ),
                    "score_category": (
                        evaluation.score_category
                        if (evaluation and shortlist.show_scores)
                        else None
                    ),
                    "client_status": item.client_status,
                    "client_comment": item.client_comment,
                    "rating": item.rating,
                }
            )

        return {
            "title": shortlist.title,
            "message_to_client": shortlist.message_to_client,
            "intro_message": shortlist.intro_message,
            "expires_at": shortlist.expires_at,
            "revoked": shortlist.revoked,
            "status": shortlist.status,
            "show_scores": shortlist.show_scores,
            "show_availability": shortlist.show_availability,
            "show_salary": shortlist.show_salary,
            "show_risks": shortlist.show_risks,
            "show_comparison": shortlist.show_comparison,
            "allow_comments": shortlist.allow_comments,
            "allow_rating": shortlist.allow_rating,
            "allow_report_download": shortlist.allow_report_download,
            "mandate": {
                "client_name": mandate.client_name if mandate else "—",
                "target_role": mandate.target_role if mandate else "—",
                "industry": mandate.industry if mandate else None,
                "city": mandate.city if mandate else None,
                "country": mandate.country if mandate else None,
            },
            "candidates": candidates_payload,
            "created_at": shortlist.created_at,
        }

    def register_view(self, shortlist: ClientShortlist) -> None:
        shortlist.viewed_count = (shortlist.viewed_count or 0) + 1
        if shortlist.viewed_at is None:
            shortlist.viewed_at = _now()
            if shortlist.status in ("ready_to_share", "invitation_sent"):
                shortlist.status = "viewed"
        self.db.add(shortlist)
        self.db.commit()

    def record_feedback(
        self,
        token: str,
        item_id: int,
        client_status: str | None,
        client_comment: str | None,
        rating: int | None = None,
    ) -> ClientShortlistItem | None:
        shortlist = self.get_by_token(token)
        if shortlist is None or shortlist.revoked:
            return None
        exp = _aware(shortlist.expires_at)
        if exp is not None and exp < _now():
            return None
        item = self.db.get(ClientShortlistItem, item_id)
        if item is None or item.shortlist_id != shortlist.id:
            return None
        if client_status is not None and client_status not in CLIENT_FEEDBACK_STATUSES:
            raise ValueError("client_status inválido")

        item.client_status = client_status
        if client_comment is not None:
            item.client_comment = client_comment
        if rating is not None and shortlist.allow_rating:
            item.rating = rating
        item.status_updated_at = _now()
        self.db.add(item)

        # Avance del status del room.
        if shortlist.status in ("viewed", "invitation_sent", "ready_to_share"):
            shortlist.status = "in_review"
        elif shortlist.status == "in_review":
            shortlist.status = "feedback_received"
        self.db.add(shortlist)

        event_type, event_label = _event_for_feedback(client_status)
        self._record_event(
            shortlist_id=shortlist.id,
            item_id=item.id,
            event_type=event_type,
            event_label=event_label,
            actor_type="client",
            metadata={"rating": rating} if rating is not None else None,
        )
        self.db.commit()
        self.db.refresh(item)
        return item

    # --- Eventos --------------------------------------------------------------

    def list_events(self, shortlist_id: int) -> list[DecisionRoomEvent]:
        return list(
            self.db.scalars(
                select(DecisionRoomEvent)
                .where(DecisionRoomEvent.shortlist_id == shortlist_id)
                .order_by(DecisionRoomEvent.created_at.desc())
            ).all()
        )

    def _record_event(
        self,
        *,
        shortlist_id: int,
        event_type: str,
        event_label: str,
        actor_type: str,
        item_id: int | None = None,
        actor_name: str | None = None,
        actor_email: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DecisionRoomEvent:
        event = DecisionRoomEvent(
            shortlist_id=shortlist_id,
            item_id=item_id,
            event_type=event_type,
            event_label=event_label,
            actor_type=actor_type,
            actor_name=actor_name,
            actor_email=actor_email,
            event_metadata=metadata or {},
        )
        self.db.add(event)
        return event


def _event_for_feedback(status: str | None) -> tuple[str, str]:
    mapping: dict[str, tuple[str, str]] = {
        "favorite": ("client_favorited", "Cliente marcó como favorito"),
        "interested": ("client_favorited", "Cliente marcó como interesado"),
        "interview_requested": ("client_requested_interview", "Cliente solicitó entrevista"),
        "want_interview": ("client_requested_interview", "Cliente solicitó entrevista"),
        "more_info_requested": (
            "client_requested_more_info",
            "Cliente pidió más información",
        ),
        "keep_in_review": ("client_kept_in_review", "Cliente mantuvo en revisión"),
        "rejected": ("client_rejected_candidate", "Cliente descartó candidato"),
        "not_interested": ("client_rejected_candidate", "Cliente descartó candidato"),
    }
    return mapping.get(status or "", ("client_commented", "Cliente registró feedback"))
