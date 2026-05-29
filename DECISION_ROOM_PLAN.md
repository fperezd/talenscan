# Decision Room — Plan de implementación

Spec fuente: `Talenscan_Decision_Room_Instrucciones_Claude_Code.docx`
Fecha inicio: 2026-05-27
Responsable técnico: Claude (Opus 4.7) bajo autorización de fperez@tooxs.com

## Principio rector

Decision Room **no es un módulo nuevo**: es la evolución del `ClientShortlist` existente. Se **extiende** la infraestructura actual (tabla `client_shortlists`, endpoints públicos por token, vista `/shortlist-cliente/[token]`, dnd-kit ya instalado para Kanban) en lugar de duplicarla. Esto respeta la sección 8 del spec y la regla obligatoria de no-regresión.

## Decisiones tomadas (2026-05-27)

| Tema | Decisión | Razón |
|---|---|---|
| Modelo de datos | Extender tabla `client_shortlists` | Spec §8 lo pide; evita migrar rooms existentes |
| Email | Modal con preview + botón copiar en v1 (sin proveedor) | Spec §7 lo permite; postergamos Resend/SES |
| Ruta cliente | Mantener `/shortlist-cliente/[token]` | Reutiliza el worker rewrite de Cloudflare |
| Estrategia entrega | Fase 1 + 2, validar en prod, luego 3–5 | Permite feedback temprano sobre el gate de seguridad |

## Diagnóstico: qué existe vs qué pide el spec

| Capacidad del spec | Estado |
|---|---|
| Token público no secuencial | ✓ `secrets.token_urlsafe(24)` |
| Items ordenados, candidato, evaluación | ✓ `order_index` |
| Vista pública + feedback | ✓ `/api/public/shortlists/{token}` |
| Toggle de score | ✓ `show_scores` |
| Expiración + revoke | ✓ `expires_at`, `revoked` |
| Código de validación 6 dígitos | ✗ |
| Estados ricos del room (draft → expired) | ✗ (solo `revoked` + `viewed_count`) |
| Estados ricos del candidato (favorite, interview, more_info, …) | ✗ (solo 3 estados: interested / not_interested / want_interview) |
| Overrides editables por el consultor (consultant_summary, why_fits, risks, evidence_level, availability, salary) | ✗ |
| Vista interna Room Builder con drag & drop | ✗ |
| Email de invitación (modal o real) | ✗ |
| Timeline de eventos | ✗ |
| Comparación ejecutiva + tab Decisiones en vista cliente | ✗ |
| `@dnd-kit` disponible | ✓ (usado en `pipeline-board.tsx`) |

## Fase 1 — Backend (gate, estados, overrides)

### 1.1 Migración Alembic `20260527_08_decision_room.py`

`client_shortlists` añadir:
- `status` VARCHAR(40) NOT NULL DEFAULT 'draft' — valores: draft, ready_to_share, invitation_sent, viewed, in_review, feedback_received, closed, expired
- `client_contact_name` VARCHAR(200) NULL
- `client_contact_email` VARCHAR(200) NULL
- `client_contact_company` VARCHAR(200) NULL
- `access_code_hash` VARCHAR(255) NULL — bcrypt o sha256 con salt
- `access_code_expires_at` TIMESTAMPTZ NULL
- `access_code_required` BOOLEAN NOT NULL DEFAULT FALSE — backward-compat: shortlists viejos no exigen código
- `last_invitation_sent_at` TIMESTAMPTZ NULL
- `intro_message` TEXT NULL — distinto de `message_to_client`; este es para el header del room
- `show_availability` BOOLEAN NOT NULL DEFAULT FALSE
- `show_salary` BOOLEAN NOT NULL DEFAULT FALSE
- `show_risks` BOOLEAN NOT NULL DEFAULT FALSE
- `show_comparison` BOOLEAN NOT NULL DEFAULT TRUE
- `allow_comments` BOOLEAN NOT NULL DEFAULT TRUE
- `allow_rating` BOOLEAN NOT NULL DEFAULT FALSE
- `allow_report_download` BOOLEAN NOT NULL DEFAULT FALSE
- `closed_at` TIMESTAMPTZ NULL

`client_shortlist_items` añadir:
- `is_pinned` BOOLEAN NOT NULL DEFAULT FALSE
- `recommendation` VARCHAR(40) NULL — highly_recommended, recommended, recommended_with_validations, reserve, not_recommended
- `consultant_summary` TEXT NULL
- `why_fits` JSONB NOT NULL DEFAULT '[]'::jsonb
- `risks_or_validations` JSONB NOT NULL DEFAULT '[]'::jsonb
- `evidence_level` VARCHAR(20) NULL — high, medium, low
- `availability` VARCHAR(200) NULL
- `salary_expectation` VARCHAR(200) NULL
- `salary_share_authorized` BOOLEAN NOT NULL DEFAULT FALSE
- `rating` SMALLINT NULL — 1–5, dejado por el cliente

Tabla nueva `decision_room_events`:
- `id` BIGSERIAL PK
- `shortlist_id` INT NOT NULL FK → client_shortlists(id) ON DELETE CASCADE, indexed
- `item_id` INT NULL FK → client_shortlist_items(id) ON DELETE SET NULL
- `event_type` VARCHAR(60) NOT NULL — room_created, candidate_added, candidate_removed, candidate_reordered, candidate_pinned, link_generated, code_generated, invitation_sent, invitation_copied, link_opened, code_validated, client_entered, client_viewed_candidate, client_favorited, client_requested_interview, client_requested_more_info, client_kept_in_review, client_rejected, client_commented, access_expired, link_regenerated, room_closed
- `event_label` VARCHAR(200) NOT NULL — texto legible en español
- `actor_type` VARCHAR(20) NOT NULL — consultant, client, system
- `actor_name` VARCHAR(200) NULL
- `actor_email` VARCHAR(200) NULL
- `metadata` JSONB NOT NULL DEFAULT '{}'::jsonb
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

Migración del enum de feedback: el constraint actual permite solo 3 valores. Pasar a 7: `favorite`, `interview_requested`, `more_info_requested`, `keep_in_review`, `rejected` + mantener `interested`/`not_interested`/`want_interview` como alias mapeados para no romper datos existentes.

### 1.2 Modelos SQLAlchemy

- Actualizar `client_shortlist.py` con todas las columnas nuevas.
- Crear `decision_room_event.py` con la entidad `DecisionRoomEvent`.
- Tupla `DECISION_ROOM_STATUSES` y `DECISION_ROOM_CANDIDATE_STATUSES` exportadas.

### 1.3 Schemas Pydantic

`schemas/client_shortlist.py`:
- Extender `ClientShortlistCreate` con `client_contact_*`, `intro_message`, `access_code_required`, todos los `show_*` y `allow_*`.
- Nuevo `ClientShortlistConfigUpdate` (PATCH parcial) — el consultor edita configuración.
- Nuevo `DecisionRoomItemOverrides` para editar consultant_summary, why_fits, risks_or_validations, recommendation, evidence_level, availability, salary, etc.
- Nuevo `DecisionRoomAccessCodeIssue` (respuesta al regenerar — devuelve código plano una sola vez).
- Nuevo `DecisionRoomAccessCodeValidate` (payload `{ code: str }`).
- Nuevo `DecisionRoomEventRead`.
- Ampliar `PublicFeedbackPayload` con los 7 estados nuevos y `rating` opcional.

### 1.4 Service `client_shortlist_service.py`

Funciones nuevas:
- `set_client_contact(shortlist_id, name, email, company)`
- `issue_access_code(shortlist_id, ttl_seconds)` → genera 6 dígitos, guarda hash, devuelve plano. Invalida el código anterior. Registra evento `code_generated`.
- `validate_access_code(token, code)` → compara contra hash, valida expiración. Si OK, registra evento `code_validated` + `client_entered` si es la primera vez. Devuelve un short-lived session token (JWT firmado o token opaco en tabla aparte — opción más simple: hash en cookie con TTL).
- `regenerate_access(shortlist_id)` → genera nuevo `public_token` + nuevo código. Invalida ambos. Registra `link_regenerated`.
- `update_room_config(...)` → toggles de visibilidad, intro_message.
- `update_item_overrides(item_id, ...)` → consultant_summary, why_fits, etc.
- `reorder_items(shortlist_id, ordered_item_ids)` → atómica.
- `pin_item(item_id, value)`.
- `record_event(...)` → helper interno usado por todas las funciones.
- `transition_status(shortlist, target)` → con guardas: draft → ready_to_share solo si hay ≥1 item; → invitation_sent solo con contacto + código; etc.

Hardening del público:
- `build_public_view` deja de devolver `score` si `show_scores=False` (ya lo hace), pero también respeta `show_availability`, `show_salary`, `show_risks`, `show_comparison`.
- Si `access_code_required=True` y la request no trae el token de sesión validado, devolver 401.

### 1.5 Endpoints nuevos

```
PATCH  /api/shortlists/{id}/config                  — toggles + intro_message + contacto
PATCH  /api/shortlists/{id}/items/{item_id}         — overrides editables del consultor
PATCH  /api/shortlists/{id}/items/reorder           — body { ordered_item_ids: [int] }
POST   /api/shortlists/{id}/items/{item_id}/pin     — body { pinned: bool }
POST   /api/shortlists/{id}/access-code             — emite código (body { ttl_hours: 24|72|168|336|720 })
POST   /api/shortlists/{id}/regenerate-access       — rota token + código
GET    /api/shortlists/{id}/events                  — timeline
POST   /api/shortlists/{id}/close                   — status = closed

POST   /api/public/shortlists/{token}/validate-code — body { code: "123456" } → { session_token, expires_at }
POST   /api/public/shortlists/{token}/items/{item_id}/feedback  — extender con 7 estados + rating
```

El público `GET /api/public/shortlists/{token}` se mantiene, pero si el room tiene `access_code_required=True`, devuelve sólo metadata mínima (cliente, cargo, expiración, requiere código) hasta que valide.

### 1.6 Tests

`apps/api/tests/test_decision_room.py`:
- `test_issue_access_code_generates_6_digits`
- `test_validate_correct_code_returns_session`
- `test_validate_wrong_code_returns_401_and_records_event` (sin filtrar info)
- `test_validate_expired_code_returns_410`
- `test_regenerate_invalidates_previous_token_and_code`
- `test_public_view_hides_salary_when_not_authorized`
- `test_public_view_hides_score_when_show_scores_false`
- `test_public_view_hides_risks_when_show_risks_false`
- `test_invalid_token_returns_404_no_data`
- `test_status_transitions_respect_guards`
- `test_event_log_records_all_state_changes`

Smoke (no-regresión):
- `test_existing_shortlist_without_code_still_works` — rooms creados antes de la migración (access_code_required=False) siguen funcionando exactamente igual.
- Pipeline, evaluaciones, reportes — no tocados, suite existente debe pasar sin cambios.

### 1.7 Deploy

1. `cd apps/api && python -m pytest -q` — todo verde local.
2. `fly deploy --remote-only -a talenscan-api`.
3. `fly ssh console -a talenscan-api -C "alembic -c alembic.ini upgrade head"`.
4. `curl https://talenscan-api.fly.dev/api/system/status` — db ok.
5. Probar manualmente: crear room nuevo desde curl, regenerar código, validar, recuperar feedback.

## Fase 2 — Frontend cliente

(Detalle se redacta al finalizar Fase 1 según lo aprendido en validación.)

- Pantalla de validación de código (`/shortlist-cliente/[token]` detecta `requires_code` y renderiza access gate antes del room).
- Modal/drawer de decisión por candidato con los 7 estados nuevos.
- Tabs: Shortlist · Comparación ejecutiva · Decisiones · Mensaje del consultor.
- Respeto a todos los toggles de visibilidad.
- Confirmación "Feedback registrado correctamente" con cambio de estado en la card.

## Fase 3 — Frontend consultor (Room Builder)

- Ruta `/mandatos/[id]/decision-room` registrada en `worker.ts` para el rewrite.
- Layout 3 zonas: header ejecutivo + builder drag&drop + panel lateral config.
- Reutiliza `@dnd-kit/core` + `@dnd-kit/sortable` ya en `package.json`.
- Edición inline de overrides por candidato.
- Preview "como cliente" en pestaña/modal nueva.
- Timeline de eventos.

## Fase 4 — Modal de invitación

- Componente `DecisionRoomInvitationModal`.
- Render del email según copy de §7 del spec (asunto, cuerpo con placeholders rellenados).
- Botón "Copiar invitación" → clipboard.
- Botón "Marcar como enviada" → registra evento `invitation_sent` y transiciona el room a `invitation_sent`.

## Fase 5 — Tests + no-regresión

- Suite Vitest/Playwright si existe; si no, smoke manual documentado.
- Verificación de las 8 funcionalidades pre-existentes (mandatos, perfil objetivo, carga CV, LinkedIn, eval 360, kanban, comparador, reportes).

## Lo que NO se toca

Carga de CV, parser, integración LinkedIn-Apify, Evaluación 360 (scoring + dimensiones), Kanban pipeline (drag & drop, stages, notas), comparador, generación Word/PDF, dashboard, config, modelos `SearchMandate` / `PositionSpec` / `Candidate` / `CandidateProfile` / `CandidateEvaluation`.

## Criterios de aceptación globales (spec §19)

Trackear contra cada item de la lista del documento al cierre de Fase 5.
