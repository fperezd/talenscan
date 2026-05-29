# Talent Market Map — Plan de implementación (CTO)

**Spec fuente:** `Talent Market Map.docx`
**Fecha:** 2026-05-29
**Responsable técnico:** Claude (Opus 4.7) bajo autorización de fperez@tooxs.com
**Stack confirmado en repo:** FastAPI + SQLAlchemy 2.0 + Pydantic + Alembic + Postgres (psycopg v3) en backend; Next.js 16 + TypeScript + Tailwind + @dnd-kit + lucide-react en frontend; OpenAI gpt-4o-mini ya integrado; Cloudflare Worker para SSG con rewrites.

---

## 1. Diagnóstico contra el código actual

### Lo que YA existe y se reutiliza tal cual

| Capacidad spec | Existe como | Reutilización |
|---|---|---|
| Mandato de búsqueda | `SearchMandate` (`apps/api/app/models/search_mandate.py`) | Lectura para generar mapa inicial |
| Perfil objetivo (industrias/empresas/cargos sugeridos) | `PositionSpec.target_industries`, `target_companies`, `equivalent_roles` (jsonb) | **Fuente primaria** del mapa inicial: ya tiene casi todo lo que necesitamos sugerir |
| Candidatos cargados | `Candidate` + `CandidateProfile.industries` + `CandidateProfile.current_company` | Para agrupar por empresa/industria/cargo |
| Evaluación 360 | `CandidateEvaluation.dimension_scores`, `critical_gaps`, `total_score`, `score_category` | Para análisis de brechas repetidas |
| Pipeline / Kanban | `CandidatePipelineItem.stage`, `is_priority`, `discard_reason` | Para cobertura y estados |
| Decision Room | `ClientShortlist` + items + feedback | Para identificar finalistas |
| OpenAI client + JSON mode + fallback | `apps/api/app/ai/openai_client.py`, `position_spec_generator.py` | **Patrón a copiar** para generación de mapa con IA |
| Dnd-kit en frontend | Pipeline Board, Decision Room | Para reordenar segmentos / empresas si lo necesitamos |
| Patrón router + service + schema | Decision Room (recién hecho) | Plantilla 1:1 |

### Lo que hay que CREAR

- 6 tablas nuevas Postgres (TalentMarketMap + MarketSegment + TargetCompany + EquivalentRole + MarketGap + RecalibrationRecommendation) + tabla pivote `MarketMapCandidate` para asociar candidatos sin tocar el modelo `Candidate`.
- Servicio IA `talent_market_map_generator.py` (genera mapa inicial + analiza candidatos + sugiere recalibraciones).
- Router `talent_market_maps.py` con ~15 endpoints REST.
- Ruta frontend `/mandatos/{id}/talent-market-map` + componente principal con 6 tabs (Resumen / Segmentos / Empresas / Cargos / Brechas / Recalibración).
- Tab nuevo en `MandatoTabs` y entry-point desde el dashboard.

### Lo que NO se toca (regla de no-regresión, igual que con Decision Room)

Carga de CVs, parser, LinkedIn-Apify, Evaluación 360, Kanban, comparador, informes Word/PDF, Decision Room, modelos `SearchMandate` / `PositionSpec` / `Candidate` / `CandidateProfile` / `CandidateEvaluation`.

---

## 2. Decisiones arquitectónicas clave

### Decisión 1: ¿Mapa por mandato (1-to-1) o por position_spec (1-to-1)?

**Recomendación: por `search_mandate_id`** con un `position_spec_id` opcional para trazar de cuál perfil se generó.

Razón: un mandato puede regenerar perfil objetivo varias veces y el mapa debe sobrevivir. Además la spec dice "por búsqueda" (= mandato), no por perfil.

### Decisión 2: ¿Generación IA o reglas determinísticas?

**Recomendación: IA por defecto, fallback determinístico (igual que `position_spec_generator`).**

- IA: genera segments + companies + equivalent roles desde mandato + perfil objetivo. Usa el mismo cliente `openai_client.py` con `JSONMode` + `field_validator` Pydantic.
- Fallback determinístico: si OpenAI falla o `OPENAI_API_KEY` está vacía, derivar segmentos directamente desde `PositionSpec.target_industries` y `target_companies`. Esto garantiza que la pantalla siempre tenga algo que mostrar.

### Decisión 3: Análisis de brechas (gap detection)

**Recomendación: motor determinístico puro, sin IA.**

Los `critical_gaps` ya están normalizados en cada `CandidateEvaluation`. Detectar brechas repetidas = `GROUP BY requirement, COUNT()` sobre los items del pipeline. No necesitamos IA. Más rápido, más barato, totalmente trazable.

Ejemplo de query:

```sql
SELECT cg->>'requirement', COUNT(*), AVG(ce.total_score)
FROM candidate_evaluations ce, jsonb_array_elements(ce.critical_gaps) cg
WHERE ce.id IN (... evals del mandato ...)
GROUP BY cg->>'requirement'
HAVING COUNT(*) >= 2
ORDER BY COUNT(*) DESC;
```

Esto es determinístico, auditable, instantáneo, y genera evidencia tangible.

### Decisión 4: Recomendaciones de recalibración (IA o reglas)

**Recomendación: híbrido.**

- Reglas determinísticas para casos obvios: "Si el 50%+ de candidatos tiene la misma brecha en `requisitos excluyentes`, sugerir relajarlo o moverlo a deseable". "Si <30% de empresas target están cubiertas, sugerir ampliar industrias adyacentes". Estas se generan automáticamente y vienen con `confidence: high`.
- IA opcional encima: sólo para redactar el copy ejecutivo de la recomendación cuando el consultor hace click en "Generar resumen IA". Esto evita inventos.

### Decisión 5: Cobertura — ¿campo precalculado o derivado en tiempo real?

**Recomendación: derivado en `build_view`, no almacenado.**

Razón: depende de pipeline_items que cambian todo el tiempo. Si lo almacenamos queda stale en seguida. El cálculo es O(N) sobre items del pipeline y es trivial.

### Decisión 6: Ruta y navegación

- Backend: `/api/mandatos/{mandate_id}/talent-market-map` (uno por mandato, idempotente al GET) + sub-recursos para segments/companies/etc.
- Frontend: `/mandatos/{id}/talent-market-map` siguiendo el patrón ya establecido por Decision Room. Tab nueva en `MandatoTabs.tsx`. Worker rewrite + matcher en `not-found.tsx` igual que `decision-room`.

### Decisión 7: ¿Necesita tabla pivote candidato↔segmento?

**Sí**, pero ligera. El spec dice "permitir filtrar candidatos por segmento, empresa, industria, cargo equivalente". Las asociaciones explícitas (overrides del consultor) van a una tabla pivote; las derivadas (auto-clasificación por `current_company`) se calculan en tiempo real.

```
market_map_candidate_overrides:
  market_map_id INT FK
  candidate_id INT FK
  segment_id INT FK NULL
  target_company_id INT FK NULL
  equivalent_role_id INT FK NULL
  manually_assigned BOOLEAN  -- si lo movió el consultor
```

---

## 3. Modelo de datos (Postgres + SQLAlchemy)

### Migración Alembic `20260529_09_talent_market_map.py`

```python
# talent_market_maps
id BIGSERIAL PK
search_mandate_id INT FK → search_mandates(id) ON DELETE CASCADE, UNIQUE  -- 1:1 por mandato
position_spec_id INT NULL FK → position_specs(id)  -- referencia al perfil usado
status VARCHAR(20) NOT NULL DEFAULT 'draft'  -- draft, generated, updated, archived
executive_summary TEXT NULL
executive_summary_for_client TEXT NULL  -- versión enviable al cliente
market_assessment VARCHAR(20) NULL  -- broad, moderate, narrow, very_narrow
generated_by_model VARCHAR(80) NULL  -- "gpt-4o-mini" o "rules-fallback"
prompt_version VARCHAR(40) NULL
generated_at TIMESTAMPTZ NULL
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at TIMESTAMPTZ NOT NULL DEFAULT now()

# market_segments
id BIGSERIAL PK
market_map_id INT FK ON DELETE CASCADE, indexed
name VARCHAR(200) NOT NULL
segment_type VARCHAR(20) NOT NULL  -- primary, adjacent, exploratory
description TEXT NULL
priority VARCHAR(10) NOT NULL DEFAULT 'medium'  -- high, medium, low
coverage_status VARCHAR(30) NOT NULL DEFAULT 'not_started'
rationale TEXT NULL
sort_order INT NOT NULL DEFAULT 0
ai_suggested BOOLEAN NOT NULL DEFAULT FALSE
created_at, updated_at TIMESTAMPTZ

# target_companies
id BIGSERIAL PK
market_map_id INT FK ON DELETE CASCADE, indexed
segment_id INT NULL FK ON DELETE SET NULL
name VARCHAR(200) NOT NULL
industry VARCHAR(120) NULL
priority VARCHAR(10) NOT NULL DEFAULT 'medium'
rationale TEXT NULL
coverage_status VARCHAR(30) NOT NULL DEFAULT 'not_reviewed'
notes TEXT NULL
ai_suggested BOOLEAN NOT NULL DEFAULT FALSE
created_at, updated_at TIMESTAMPTZ
-- candidatos asociados se calculan en tiempo real, no se cachean

# equivalent_roles
id BIGSERIAL PK
market_map_id INT FK ON DELETE CASCADE, indexed
title VARCHAR(200) NOT NULL
seniority VARCHAR(80) NULL
closeness VARCHAR(10) NOT NULL DEFAULT 'medium'  -- high, medium, low
rationale TEXT NULL
priority VARCHAR(10) NOT NULL DEFAULT 'medium'
industries JSONB NOT NULL DEFAULT '[]'  -- industrias donde aparece
ai_suggested BOOLEAN NOT NULL DEFAULT FALSE
created_at, updated_at TIMESTAMPTZ

# market_gaps  (determinísticos, calculados desde evaluaciones)
id BIGSERIAL PK
market_map_id INT FK ON DELETE CASCADE, indexed
title VARCHAR(200) NOT NULL  -- "Inglés no evidenciado"
frequency INT NOT NULL  -- 5 (= 5 de los N evaluados lo tienen)
total_evaluated INT NOT NULL  -- N
impact VARCHAR(10) NOT NULL DEFAULT 'medium'
evidence TEXT NULL
recommendation TEXT NULL
detected_at TIMESTAMPTZ NOT NULL DEFAULT now()

# recalibration_recommendations
id BIGSERIAL PK
market_map_id INT FK ON DELETE CASCADE, indexed
title VARCHAR(200) NOT NULL
reason TEXT NOT NULL
expected_impact TEXT NULL
confidence VARCHAR(10) NOT NULL DEFAULT 'medium'
status VARCHAR(12) NOT NULL DEFAULT 'suggested'  -- suggested, accepted, rejected
generated_by VARCHAR(20) NOT NULL DEFAULT 'rules'  -- rules, ai
acted_at TIMESTAMPTZ NULL
created_at TIMESTAMPTZ NOT NULL DEFAULT now()

# market_map_candidate_overrides  (asociaciones explícitas)
id BIGSERIAL PK
market_map_id INT FK ON DELETE CASCADE, indexed
candidate_id INT FK ON DELETE CASCADE, indexed
segment_id INT NULL FK ON DELETE SET NULL
target_company_id INT NULL FK ON DELETE SET NULL
equivalent_role_id INT NULL FK ON DELETE SET NULL
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
UNIQUE (market_map_id, candidate_id)
```

### Por qué este modelo

- **CASCADE en FK al market_map**: borrar/archivar mapa limpia todo, evita huérfanos.
- **JSONB sólo donde necesitamos flexibilidad** (`industries` en equivalent_roles), todo lo demás columnas relacionales = filtrable + indexable.
- **`ai_suggested` flag**: trazabilidad de qué generó la IA vs qué creó el consultor. Sirve para "regenerar IA" sin pisar lo manual.
- **`market_gaps` regenerable**: la tabla se reescribe entera cuando se recalcula. No es write-heavy.
- **Pivote `market_map_candidate_overrides`** sólo para asociaciones manuales. Las derivadas (candidato cuya empresa coincide con una target_company) se calculan al vuelo.

---

## 4. Endpoints API

```
# Map maestro
GET    /api/mandatos/{mandate_id}/talent-market-map          → obtener o crear vacío
POST   /api/mandatos/{mandate_id}/talent-market-map/generate → generar/regenerar con IA
PATCH  /api/talent-market-maps/{id}                          → editar executive_summary, status
DELETE /api/talent-market-maps/{id}                          → archivar (no borrar)

# Segments
POST   /api/talent-market-maps/{id}/segments
PATCH  /api/talent-market-maps/{id}/segments/{seg_id}
DELETE /api/talent-market-maps/{id}/segments/{seg_id}
PATCH  /api/talent-market-maps/{id}/segments/reorder

# Companies
POST   /api/talent-market-maps/{id}/companies
PATCH  /api/talent-market-maps/{id}/companies/{co_id}
DELETE /api/talent-market-maps/{id}/companies/{co_id}

# Equivalent roles
POST   /api/talent-market-maps/{id}/equivalent-roles
PATCH  /api/talent-market-maps/{id}/equivalent-roles/{role_id}
DELETE /api/talent-market-maps/{id}/equivalent-roles/{role_id}

# Gaps (regenerar)
POST   /api/talent-market-maps/{id}/gaps/recompute          → re-corre análisis sobre evaluaciones

# Recommendations
POST   /api/talent-market-maps/{id}/recommendations/regenerate
PATCH  /api/talent-market-maps/{id}/recommendations/{rec_id} → status=accepted|rejected

# Candidatos
POST   /api/talent-market-maps/{id}/candidates/{cand_id}/assign  → asignar a segment/company/role
DELETE /api/talent-market-maps/{id}/candidates/{cand_id}/assign
GET    /api/talent-market-maps/{id}/candidates                   → lista con filtros derivados

# Exportar / copiar resumen
GET    /api/talent-market-maps/{id}/export/summary               → texto plano para copiar
POST   /api/talent-market-maps/{id}/summary/regenerate-with-ai   → re-redacta executive_summary
```

### Endpoint público / cliente

**No requiere endpoint público.** El Talent Market Map es 100% interno del consultor. Si en el futuro se quiere exponer al cliente, se agrega un wrapper similar a Decision Room.

---

## 5. Servicios backend

### `services/talent_market_map_service.py`

Responsabilidades:
- CRUD del mapa y sus sub-entidades
- `generate_from_mandate(mandate_id)`: orquesta generación inicial
- `recompute_coverage(map_id)`: calcula cobertura en tiempo real
- `detect_gaps(map_id)`: corre el query SQL y persiste en `market_gaps`
- `generate_recommendations(map_id)`: reglas determinísticas
- `build_view(map_id)`: serializa todo el mapa para el frontend (con cobertura calculada al vuelo)

### `ai/talent_market_map_generator.py`

Sigue el patrón de `position_spec_generator.py`:
- Recibe mandato + perfil objetivo
- Prompt estructurado
- JSON mode
- Validación con Pydantic
- Fallback determinístico si OpenAI falla

Schema de output esperado de OpenAI:

```json
{
  "executive_summary": "string (200-400 palabras)",
  "market_assessment": "broad|moderate|narrow|very_narrow",
  "segments": [
    {"name": "...", "segment_type": "primary|adjacent|exploratory", "description": "...", "priority": "...", "rationale": "..."}
  ],
  "companies": [
    {"name": "...", "industry": "...", "segment_name": "...", "priority": "...", "rationale": "..."}
  ],
  "equivalent_roles": [
    {"title": "...", "seniority": "...", "closeness": "...", "industries": [...], "rationale": "..."}
  ]
}
```

Prompt va en español, instrucciones claras de no inventar, debe basarse en mandato + perfil. Reuse `model_version` + `prompt_version` para auditoría.

### `scoring/gap_detector.py`

Función pura:
- Input: `list[CandidateEvaluation]`
- Output: `list[MarketGap]` con frequency, impact, evidence
- Lógica: agrupa por `critical_gap.requirement`, calcula frequency y promedio de impact desde el campo `impact` de cada gap.

### `scoring/recommendation_engine.py`

Reglas determinísticas, ej.:

```python
def generate_recommendations(map_, evaluations, coverage):
    recs = []
    if coverage.pct < 30 and len(map_.target_companies) > 0:
        recs.append(Rec(title="Ampliar empresas target", reason=..., confidence="high"))
    if any_gap_freq_above(evaluations, 0.5, severity="excluyente"):
        recs.append(Rec(title="Relajar requisito excluyente X", reason=..., confidence="high"))
    if avg_score_below(evaluations, 60):
        recs.append(Rec(title="Revisar calibración del perfil objetivo", reason=..., confidence="medium"))
    # ... ~8-10 reglas
    return recs
```

---

## 6. Frontend

### Estructura

```
apps/web/
  app/mandatos/[id]/talent-market-map/page.tsx       (SSG con generateStaticParams demo)
  components/talent-market-map/
    talent-market-map.tsx                            (componente raíz, fetches + tabs)
    header.tsx                                       (KPIs + acciones)
    executive-summary-card.tsx                       (resumen editable + botón regenerar IA)
    coverage-panel.tsx                               (barras + donut simple)
    segments-tab.tsx                                 (cards de segmentos editables + dnd-kit reorder)
    companies-tab.tsx                                (tabla con filtros y edit inline)
    equivalent-roles-tab.tsx                         (cards con closeness badge)
    gaps-tab.tsx                                     (tabla agrupada con barras de frecuencia)
    recalibration-tab.tsx                            (cards aceptar/rechazar)
    candidates-side-panel.tsx                        (drawer para asignar a segmento/empresa/rol)
    coverage-donut.tsx                               (SVG inline, no chart lib)
    add-company-modal.tsx
    add-segment-modal.tsx
    add-equivalent-role-modal.tsx
  types/talent-market-map.ts                         (todos los tipos)
```

### Tabs

| Tab | Contenido principal |
|---|---|
| Resumen | Executive summary editable + coverage panel + counts |
| Segmentos | Cards de 3 tipos (primary/adjacent/exploratory) + dnd reorder |
| Empresas | Tabla filtrable por segmento/industria/cobertura |
| Cargos equivalentes | Cards con closeness y candidatos asociados |
| Brechas | Tabla con barras horizontales de frecuencia + recomendaciones |
| Recalibración | Cards con CTA aceptar/rechazar |

### Componentes UI

- Usar el mismo lenguaje visual que Decision Room (cards, badges, headers ejecutivos, paleta `brand-blue`/`brand-blueSoft`)
- Donut de cobertura: SVG inline simple (no Recharts/Chart.js — política de no agregar deps)
- Barras de brechas: divs con `w-[XX%]` (mismo patrón que Decision Room dimension bars)

### Integración con resto de la app

- Botón "Talent Market Map" en `MandatoTabs.tsx` (junto a Pipeline / Decision Room)
- Widget en dashboard: "Mapas con recomendaciones pendientes" (cuenta de `recalibration_recommendations` en status=`suggested` con confidence=`high` sumados across maps)
- Worker rewrite + matcher en `not-found.tsx` (igual que decision-room)

---

## 7. Plan por fases con entregables

| Fase | Scope | Entregable | Esfuerzo |
|---|---|---|---|
| **F1 — Fundación** | Migración Alembic 09, modelos, schemas, service base sin IA, endpoint GET/POST/PATCH del mapa maestro, CRUD de segments/companies/equivalent-roles | Backend con tests | 1.5 días |
| **F2 — Generación IA + fallback** | `talent_market_map_generator.py` con OpenAI JSON mode + Pydantic + fallback determinístico desde `PositionSpec`. Endpoint `/generate`. Tests con mock | Generación funciona end-to-end | 1 día |
| **F3 — Análisis determinístico** | `gap_detector` + `recommendation_engine` + endpoints `/gaps/recompute` y `/recommendations/regenerate` + cobertura derivada en `build_view` | Datos accionables visibles | 1 día |
| **F4 — Frontend base** | Ruta + componente raíz + header + tabs vacías + types + integración con `MandatoTabs` + worker rewrite + not-found | Pantalla navegable | 1 día |
| **F5 — Tabs ricas** | Implementación de las 6 tabs con edit inline, dnd reorder en segmentos, filtros en empresas, barras en brechas, aceptar/rechazar en recalibración | UX premium completa | 2 días |
| **F6 — Asignación de candidatos** | Side-panel drawer para asociar candidatos a segments/companies/roles, filtros derivados | Mapa conectado a candidatos | 1 día |
| **F7 — Exportar resumen** | Endpoint `/export/summary` (texto plano), botón copiar al portapapeles, botón "Regenerar resumen con IA" | Entregable al cliente | 0.5 día |
| **F8 — Integraciones + dashboard** | Botón desde detalle mandato, widget en dashboard, link desde Decision Room ("ver mapa de mercado") | Discoverable | 0.5 día |
| **F9 — Tests + no-regresión + deploy** | Tests backend nuevos, smoke E2E, validación de no-regresión sobre Decision Room/Pipeline/etc, deploy backend + frontend | En prod | 0.5 día |

**Total estimado: ~9 días de trabajo enfocado.**

### Hitos validables (para que el usuario testee y dé feedback)

- **Después de F2**: el usuario puede llamar `POST /generate` por curl y ver el JSON resultante. Permite validar la calidad del prompt antes de invertir en UI.
- **Después de F4**: pantalla navegable con datos mock. Decide UX antes de pulir.
- **Después de F5**: producto presentable comercialmente.
- **Después de F9**: integración completa.

Recomiendo entregar **F1+F2+F3 (backend completo, ~3.5 días)** como primer ciclo cerrado y validar generación IA con datos reales, luego **F4+F5+F6 (frontend, ~4 días)** como segundo ciclo. F7-F9 como tercer ciclo.

---

## 8. Riesgos y mitigación

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| OpenAI genera segmentos / empresas inventadas | Media | Alto (credibilidad del producto) | Prompt explícito de "basarte en el perfil objetivo y mandato dados"; mostrar fuente (`ai_suggested=true`); permitir edición y rechazo manual; auditar en `prompt_version` |
| Roles del CV vienen mal parseados (ya pasa hoy) → contamina análisis por empresa | Alta | Medio | Falla en silencio: si `Candidate.current_company` es ruido, no aparece como match automático. El consultor puede asignar manual |
| Performance: `build_view` con cobertura + asignaciones derivadas puede ser lento si hay 100+ candidatos en el mandato | Media | Bajo (MVP no tiene esos volúmenes) | Precalcular cobertura en cache en memoria por request; índices en `pipeline_items.mandate_id` ya existen |
| Doble fuente de verdad (segmentos derivados del perfil vs segmentos manuales) confunde al consultor | Media | Medio | Flag `ai_suggested` en cada entidad + badge UI claro ("Sugerido por IA" / "Agregado por consultor") |
| El consultor regenera con IA y pierde su edición manual | Alta | Alto | Botón "Regenerar" sólo afecta entidades con `ai_suggested=true` y status no editado; confirmar con modal si va a pisar overrides |
| Spec dice "exportable o copiable" y "Word/PDF no se rompe" → tentación de generar PDF aquí | Baja | Bajo | Primera versión: copiar texto al portapapeles. PDF dedicado queda fuera de scope F1 |
| Migración Alembic con 7 tablas nuevas falla parcial en prod | Baja | Alto | Migración atómica en transacción (default Alembic); rollback testeado local; deploy fuera de horario peak |

---

## 9. Decisiones que necesito antes de codear

| Pregunta | Recomendación CTO | Alternativas |
|---|---|---|
| ¿Generación IA por default al primer GET o sólo bajo botón "Generar"? | **Sólo bajo botón explícito** | Auto-generar es cómodo pero gasta OpenAI tokens sin demanda |
| ¿1 mapa por mandato (UNIQUE) o varios versionados? | **1 mapa por mandato** (UNIQUE en `search_mandate_id`) | Versionado da auditoría pero complica UX |
| ¿Cobertura derivada incluye candidatos sólo cargados o sólo evaluados? | **Configurable, default = evaluados** | El spec habla de ambos en distintas partes |
| ¿Recalcular brechas automáticamente al crear evaluación nueva? | **No; botón "Recalcular brechas"** | Auto-recalcular implica hook en EvaluationService → acopla módulos |
| ¿Mostrar el mapa también al cliente en el Decision Room? | **No en v1** (spec lo deja fuera) | Es interesante pero suma scope |
| ¿Quién está autorizado a regenerar con IA / aceptar recomendaciones? | **Cualquier usuario** (no hay roles aún) | Cuando entre auth real, agregar permisos |

---

## 10. Métricas de éxito post-launch

Cuando el usuario empiece a usarlo en producción, voy a quere monitorear:

- **% de mandatos activos con un Talent Market Map generado** (objetivo: ≥80% en 30 días)
- **# de recomendaciones aceptadas vs rechazadas** (señal de calidad de las reglas/IA; objetivo: >40% accepted)
- **# de empresas target agregadas manualmente** vs sugeridas (señal de si la IA capta bien el mercado)
- **Tiempo desde "Generar mapa" hasta "primera edición manual"** (engagement)
- **# de brechas detectadas con frequency ≥ 3** (sirve para validar que el motor de brechas funciona)

Endpoint trivial: `GET /api/system/talent-market-map-metrics` (interno, no público).

---

## 11. Fuera de alcance v1 (explícito en spec)

- Scraping nuevo (LinkedIn / empresas)
- Datos salariales externos
- Benchmark de compensación
- Predicción estadística avanzada
- Compra de bases externas
- Integración LinkedIn Recruiter
- Multi-usuario / permisos
- Exportar PDF/Word del mapa (sólo texto copiable en v1)

---

## 12. Resumen ejecutivo (para presentar al usuario)

**Qué construimos:** un módulo interno por mandato que mapea industrias, empresas y cargos equivalentes del mercado objetivo, mide cobertura usando los datos que ya están en Talenscan (pipeline + evaluaciones + Decision Room), detecta brechas repetidas en candidatos y sugiere recalibraciones del perfil. Todo editable y trazable.

**Cómo se construye:**
- Backend: 7 tablas nuevas, 1 servicio principal, 1 generador IA + fallback, 1 motor de reglas para brechas y recomendaciones, ~15 endpoints REST.
- Frontend: 1 ruta nueva con 6 tabs siguiendo el lenguaje visual de Decision Room. Reutilizamos `@dnd-kit`, Tailwind, lucide-react ya instalados.
- IA: gpt-4o-mini (ya configurada) con JSON mode + fallback determinístico. Mismo patrón que `position_spec_generator`.

**Cuánto cuesta construirlo:** ~9 días de trabajo enfocado, dividido en 3 ciclos validables (backend 3.5d → frontend 4d → integraciones y deploy 1.5d).

**Qué riesgo de no-regresión:** Bajo. No tocamos Decision Room, Pipeline, Evaluación 360, ni los modelos base. Sólo agregamos tablas y rutas.

**Qué necesita confirmar el usuario antes de codear:** las 6 decisiones de la sección 9, principalmente:
1. Generación IA bajo botón explícito (no auto)
2. 1 mapa por mandato (no versionado)
3. Tab desde detalle mandato, igual que Decision Room
