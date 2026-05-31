# Autenticación + Multi-tenancy — Plan (CTO)

**Fecha:** 2026-05-31
**Decisión final:** **auth self-hosted en Fly** (FastAPI sobre el Postgres propio), auto-registro **self-service**, **multi-tenant** (datos aislados por organización).

> Evolución de la decisión: Clerk → Supabase → **self-hosted en Fly**. Motivo: el usuario prefiere quedarse en su stack (Fly), sin vendor extra ni segunda base de datos. Todo corre donde ya está el backend.

---

## 1. Requerimiento

- SSO **Microsoft (Entra)** y **Google**, **solo cuentas empresariales** (no gmail/personal).
- **Email + contraseña** con auto-registro.
- Cada empresa = **organización** con **datos aislados**.

## 2. Arquitectura (todo en Fly)

- **Backend FastAPI** es el Identity Provider: emite y verifica sus propios **JWT de sesión (HS256)** con `auth_jwt_secret`. Hash de password con **scrypt (stdlib)**. Sin dependencias nuevas.
- **Frontend estático**: pantallas de sign-up/in que llaman a `/api/auth/*`; guarda el JWT y lo manda en `Authorization: Bearer`. SSO redirige al backend (`/api/auth/oauth/...`).
- **Una sola base de datos** (Fly Postgres): `organizations`, `users` (con `password_hash`, `email_verified`, `oauth_*`) + el resto de la app.

## 3. Verificación "solo empresa" (IMPLEMENTADO + TESTEADO)

`app/core/auth.py`: `is_business_email` (denylist de dominios de consumo, configurable) + `assert_business_account` (Google exige `hd` de Workspace; Microsoft rechaza tenant personal MSA). Aplica a email/password y a SSO.

## 4. Modelo multi-tenant

- `organizations` (name, primary_domain, plan) + `users` (email único, role, password_hash, oauth_*). Migración 11 lista. **Org por dominio de email**: el primer usuario de un dominio crea la org y es `owner`; los siguientes son `member` de la misma org.
- `organization_id` (FK) en tablas raíz + scoping por org en cada query (P4, pendiente).

## 5. Fases

| Fase | Alcance | Estado |
|---|---|---|
| **P1 — Foundation** | Modelos org/user + migración 11; regla solo-empresa; password hashing; JWT propio (emisión+verificación) | ✅ HECHO |
| **P2 — Email/password** | `/api/auth/register`, `/login`, `/me`; org por dominio; service + 25 tests | ✅ HECHO |
| **P3 — SSO Google/Microsoft** | Router OAuth (authorization-code con authlib/httpx): start + callback, `assert_business_account` sobre claims, `upsert_oauth_user`, emite JWT propio | Pendiente (requiere OAuth client id/secret) |
| **P4 — Frontend** | Pantallas sign-up/in (email+password + botones SSO) + gate sobre AppShell + token en `apiFetch` | Pendiente |
| **P5 — Scoping de datos** | `organization_id` en tablas raíz + enforcement por módulo + backfill | Pendiente (el grueso, ~semanas) |
| **P6 — Cutover** | `require_principal` en todos los endpoints; org_id NOT NULL; retirar API key interino | Pendiente |
| **(opcional)** | Verificación de email + reset de password (requiere un sender SMTP/Resend) | Pendiente |

## 6. Checklist del USUARIO (desbloquea P3)

1. **Google**: en Google Cloud Console → OAuth 2.0 Client (Web). Redirect URI: `https://talenscan-api.fly.dev/api/auth/oauth/google/callback`. Pasar **client id + secret** (Fly secrets).
2. **Microsoft**: Azure → App registrations. "Accounts in any organizational directory" (work/school, NO personal). Redirect: `https://talenscan-api.fly.dev/api/auth/oauth/microsoft/callback`. Pasar **client id + secret** (Fly secrets).
3. En prod: `fly secrets set AUTH_JWT_SECRET=<random largo>` (firma de sesiones), `OAUTH_REDIRECT_BASE=https://talenscan-api.fly.dev`.
4. (Email verification/reset, opcional) elegir sender (Resend/SMTP) y pasar credenciales.

## 7. Estado en prod

Nada de auth está deployado aún. La API en prod sigue abierta hasta el cutover (P6) o hasta activar el **API key interino** (`app/core/security.py`, `fly secrets set API_KEY=...`).
