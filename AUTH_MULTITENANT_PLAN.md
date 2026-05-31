# Autenticación + Multi-tenancy — Plan de implementación (CTO)

**Fecha:** 2026-05-30
**Decisiones del usuario:** auto-registro **self-service** + auth con **Supabase Auth** + **multi-tenant completo** (datos aislados por organización).

> Descartado: Clerk (no querían atarse). Cloudflare Access se evaluó pero no cubre "email+password self-service" (solo SSO + PIN). Fly no tiene producto de auth.

---

## 1. Requerimiento

- SSO **Microsoft (Entra)** y **Google**, **solo cuentas empresariales** (no gmail/outlook/personal).
- **Email + contraseña** con auto-registro.
- Cada empresa = **organización** con **datos aislados**.

## 2. Arquitectura

- **Frontend** (Next `output:'export'` estático + Worker): usa **`@supabase/supabase-js`** client-side para sign-up/in (email+password y OAuth Google/Microsoft). Obtiene un **JWT de sesión** y lo manda al backend en `Authorization: Bearer`.
- **Backend FastAPI** = resource server: **verifica el JWT de Supabase (HS256 con el JWT secret del proyecto)** — sin dependencias externas (stdlib). Extrae `sub` (uuid) + `email`. **YA IMPLEMENTADO Y TESTEADO** (`app/core/auth.py::verify_supabase_jwt`).
- **Organizaciones**: Supabase Auth no tiene orgs → las modelamos nosotros (`organizations` + `users`). En el primer login se sincroniza el usuario y se resuelve/crea su organización (por dominio de email).

## 3. Verificación "solo empresa" (IMPLEMENTADO)

`app/core/auth.py`:
- `is_business_email()`: denylist de dominios de consumo (gmail, outlook, hotmail, yahoo, icloud, proton, aol, gmx, yandex, qq, 163…), configurable por env.
- `assert_business_account()`: además exige Google Workspace (claim `hd`) y rechaza cuenta Microsoft personal (MSA tenant). Aplica también a email/password.
- Refuerzo recomendado en Supabase: **Auth Hook "before user created"** (Edge Function) que rechaza dominios de consumo en el alta, para no depender solo del backend.

## 4. Modelo multi-tenant

- `organizations` (name, primary_domain, plan) y `users` (`auth_user_id` = uuid de Supabase, `organization_id` FK, email, role). **Migración 11 lista.**
- `organization_id` (FK) en tablas raíz (`search_mandates`, `candidates`, `talent_profiles`, `client_shortlists`, `talent_market_maps`); hijas heredan vía su raíz.
- Dependencia `get_current_org_id` + helper de scoping; toda query filtra por la org del principal. Org default mientras se migra.

## 5. Fases

| Fase | Alcance | Estado |
|---|---|---|
| **P1 — Foundation** | Modelos org/user + migración 11; `is_business_email`/`assert_business_account`; dependencia `get_current_principal` env-gated | ✅ HECHO |
| **P2 — Verificación JWT** | `verify_supabase_jwt` (HS256, stdlib) + extracción de principal | ✅ HECHO (falta solo el secret real del proyecto) + pendiente sync user/org en primer login |
| **P3 — Frontend** | `@supabase/supabase-js` + pantallas sign-up/in (email+password + OAuth Google/MS) + gate sobre AppShell + token en `apiFetch` | Pendiente (requiere proyecto Supabase) |
| **P4 — Scoping de datos** | `organization_id` en cada tabla raíz + enforcement por módulo + backfill a org default | Pendiente (el grueso) |
| **P5 — Cutover** | org_id NOT NULL, exigir auth en todos los endpoints, retirar API key interino | Pendiente |

**Estimación realista:** 2–4 semanas (P4 es el grueso).

## 6. Checklist de setup del USUARIO (desbloquea P2-sync/P3)

1. Crear proyecto en **Supabase** (supabase.com). Anotar: `Project URL`, `anon key` (frontend), **`JWT secret`** (Settings → API → JWT, para el backend).
2. **Auth → Providers**: habilitar **Email** (con confirmación), **Google** y **Azure (Microsoft)**.
   - Google: crear OAuth client en Google Cloud Console; redirect a `https://<ref>.supabase.co/auth/v1/callback`.
   - Microsoft: App registration en Azure (work/school, no personal); mismo redirect.
3. **Restringir dominios** (recomendado): Auth Hook "before user created" que rechace dominios de consumo (o validamos solo en backend, ya implementado).
4. **URL Configuration**: Site URL + redirect = `https://talenscan-web.tooxs-fperez.workers.dev`.
5. Pasar al backend (Fly secret): `SUPABASE_JWT_SECRET`, `SUPABASE_URL`. Al frontend: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`.

## 7. Interino (ya en prod tras deploy)

Middleware **API key** (`app/core/security.py`, env-gated) activable con `fly secrets set API_KEY=...` + `NEXT_PUBLIC_API_KEY=...` para sacar la API de estar 100% abierta mientras llega Supabase. Se retira en P5.
