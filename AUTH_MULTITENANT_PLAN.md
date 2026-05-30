# Autenticación + Multi-tenancy — Plan de implementación (CTO)

**Fecha:** 2026-05-30
**Decisiones del usuario:** proveedor gestionado + multi-tenant completo.
**Proveedor elegido:** **Clerk** (Organizations nativas, email/password, social Google/Microsoft, SDK para frontend estático, free tier amplio). Reversible a WorkOS si más adelante el foco es SAML enterprise.

---

## 1. Requerimiento

- SSO con **Microsoft (Entra)** y **Google**, **solo cuentas empresariales** (no gmail/outlook/personal) → verifica la empresa.
- **Email + contraseña** como alternativa de registro.
- Cada empresa = **organización** con **datos aislados** (multi-tenant).

## 2. Restricción arquitectónica

El frontend es **Next.js `output: 'export'` (estático)** servido por un Cloudflare Worker: no hay servidor Next ni API routes. Por eso:
- La auth vive **client-side** con el **SDK de Clerk React** (`@clerk/clerk-react`), que maneja UI de sign-in/up, social SSO, email/password y el switcher de organización.
- El **backend FastAPI** actúa como **resource server**: valida el **JWT de sesión de Clerk** (RS256 vía JWKS), extrae `user_id`, `org_id` y `email`, y **scopea todas las queries por organización**.

## 3. Verificación "solo empresa"

Triple control (defensa en profundidad):
1. **Clerk dashboard**: restringir dominios (blocklist de proveedores de consumo) y configurar las social connections.
2. **En el token / claims**:
   - Google: exigir presencia del claim `hd` (Google Workspace). Sin `hd` = cuenta personal → rechazar.
   - Microsoft: exigir cuenta *work/school* (Entra `tid` de tenant, no MSA personal/`9188040d-6c67-4c5b-b112-36a304b66dad`).
3. **Backend `is_business_email()`** (implementado y testeado en `app/core/auth.py`): denylist de dominios de consumo (gmail, outlook, hotmail, live, yahoo, icloud, proton, aol, gmx, yandex, qq, 163…). Se aplica también al registro email/password.

## 4. Modelo multi-tenant

- Nuevas tablas: **`organizations`** (espejo local de la org de Clerk: `clerk_org_id`, name, domain, plan) y **`users`** (`clerk_user_id`, `organization_id` FK, email, full_name, role).
- **`organization_id`** (FK nullable en la fase de transición) en las tablas raíz: `search_mandates`, `candidates`, `talent_profiles`, `client_shortlists`, `talent_market_maps`. Las tablas hijas heredan el scoping vía su raíz (join).
- Toda query de lectura/escritura se filtra por el `organization_id` del principal autenticado. Un helper `scoped(query, org_id)` + dependencia `get_current_org` centraliza el patrón.

## 5. Fases (incremental, sin romper prod)

| Fase | Alcance | Estado |
|---|---|---|
| **P1 — Foundation** | Modelos Organization+User + migración 11, `is_business_email`/`assert_business_account`, dependencia de auth env-gated (inerte sin claves Clerk), config `clerk_*`, tests | **HECHO (esta sesión)** |
| **P2 — Verificación JWT real** | Plug de JWKS de Clerk (PyJWT) en `verify_session_token`; webhook de Clerk para sincronizar org/user a las tablas locales | Pendiente (requiere claves Clerk) |
| **P3 — Frontend** | `@clerk/clerk-react` (ClerkProvider + `<SignIn/>`/`<SignUp/>` + gate que envuelve AppShell + `<OrganizationSwitcher/>`); `apiFetch` envía el token; restricción de dominios | Pendiente (requiere claves Clerk) |
| **P4 — Scoping de datos** | Agregar enforcement de `organization_id` en cada service/router (módulo por módulo, con tests). Backfill de filas existentes a una org default | Pendiente |
| **P5 — Cutover** | Activar enforcement (org_id NOT NULL), exigir auth en todos los endpoints, retirar el API key interino | Pendiente |

**Estimación realista:** 2–4 semanas de trabajo enfocado (P4 es el grueso: tocar cada módulo + tests + backfill).

## 6. Checklist de setup del USUARIO (bloquea P2/P3)

Esto no lo puedo hacer yo (requiere tus cuentas):

1. **Crear cuenta y app en Clerk** (clerk.com). Anotar `CLERK_PUBLISHABLE_KEY` (frontend) y `CLERK_SECRET_KEY` (backend).
2. **Habilitar Organizations** en el dashboard de Clerk.
3. **Email + Password**: habilitar como método.
4. **Google**: en Google Cloud Console crear OAuth 2.0 Client (Web), agregar los redirect URIs de Clerk; pegar client id/secret en Clerk. (Para forzar Workspace: validar `hd` en backend; opcionalmente Enterprise SSO de Clerk.)
5. **Microsoft**: en Azure Portal → App registrations, crear app, configurar redirect de Clerk, exponer client id/secret; pegarlos en Clerk. Configurar "Accounts in any organizational directory" (work/school), NO personal.
6. **Restringir dominios**: en Clerk, blocklist de dominios de consumo (o allowlist del/los dominios de tus clientes).
7. **Redirect/allowed origins** en Clerk: agregar `https://talenscan-web.tooxs-fperez.workers.dev`.
8. Pasar a backend (Fly secret) y frontend (`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`): las claves. Yo cableo el código en P2/P3.

## 7. Interino (ya en prod tras deploy)

Mientras llega Clerk, el middleware **API key** (`app/core/security.py`, env-gated) puede activarse con `fly secrets set API_KEY=...` + `NEXT_PUBLIC_API_KEY=...` para sacar la API de estar 100% abierta. Se retira en P5.
