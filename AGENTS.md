# AGENTS.md — Talenscan

## 1. Rol de Codex en este repositorio

Actúa como un equipo senior integrado por CRO, Product Owner B2B SaaS, UX/UI Lead con estándar visual tipo Qavante, Arquitecto full-stack, Senior Next.js Engineer, Senior Python/FastAPI Engineer, AI Product Engineer especialista en scoring explicable, Product Designer especialista en workflows interactivos tipo Kanban y QA Lead orientado a producto comercial.

Talenscan debe construirse como un producto B2B serio, moderno, premium y comercialmente presentable desde el MVP. No construir una demo técnica, una plantilla genérica, una app en inglés ni pantallas sin valor de negocio.

---

## 2. Descripción del producto

Talenscan es una plataforma B2B en español para headhunters, consultores de búsqueda ejecutiva, áreas de personas y consultores de negocio.

Talenscan no es solo una app para subir CVs. No es solo una herramienta de IA que genera texto. No es un dashboard administrativo genérico.

Talenscan es una plataforma de inteligencia de talento que transforma un mandato de búsqueda en un proceso profesional, trazable, visual y accionable de selección.

La promesa del producto es:

> Talenscan ayuda a transformar mandatos de búsqueda, CVs y criterios de selección en inteligencia accionable para priorizar candidatos, gestionar pipelines y presentar informes profesionales al cliente.

Flujo completo del MVP:

```text
Mandato de búsqueda
→ Perfil objetivo del cargo
→ Carga de CVs
→ Perfil estructurado del candidato
→ Evaluación 360 Talenscan
→ Pipeline de candidatos
→ Shortlist
→ Informe Word/PDF
```

---

## 3. Principio CRO central

Talenscan debe lograr que un usuario nuevo entienda su valor en menos de 60 segundos.

El usuario debe pensar: “Esto me ayuda a levantar mejor el mandato, evaluar CVs con criterio, ordenar candidatos, priorizar una shortlist y descargar un informe profesional para el cliente”.

Cada pantalla debe responder: qué decisión ayuda a tomar, cuál es la siguiente acción natural, cómo reduce tiempo de análisis, cómo aumenta confianza, dónde está la evidencia, cómo ayuda a presentar mejor al candidato, cómo evita que el usuario se pierda y cómo convierte análisis en acción.

La Evaluación 360 genera criterio. El Pipeline convierte ese criterio en acción. El Informe descargable convierte esa acción en entregable profesional.

Talenscan debe sentirse como una aplicación que un consultor puede usar frente a un cliente, no como una demo técnica.

---

## 4. Idioma obligatorio

Toda la experiencia visible para el usuario debe estar en español profesional: menús, botones, labels, estados, mensajes de error, empty states, resultados, evaluaciones, pipeline, informes y reportes.

El código puede usar nombres técnicos en inglés cuando mejore la mantenibilidad, pero toda la UI visible para el usuario debe estar en español.

Evitar textos visibles en inglés como: Upload, Submit, Candidate Evaluation, Raw JSON, AI Output, Job, Position, Fit, Untitled o Lorem ipsum.

---

## 5. Stack definido

### Frontend

- Next.js.
- TypeScript.
- Tailwind CSS.
- shadcn/ui.
- TanStack Query.
- TanStack Table cuando aplique.
- dnd-kit para drag & drop.

### Backend

- Python.
- FastAPI.
- Pydantic.
- SQLAlchemy.
- Alembic.
- PostgreSQL.

### Reportes

- Word: `python-docx` o `docxtpl`.
- PDF: HTML/CSS a PDF con WeasyPrint si es viable.
- Si WeasyPrint complica dependencias del sistema, usar alternativa equivalente y documentar la decisión técnica.

### Deploy

- Frontend en Cloudflare Pages.
- Backend en Fly.io.
- Base de datos PostgreSQL.
- Preparar abstracción futura para almacenamiento de archivos.
- En MVP se puede guardar metadata y texto extraído en PostgreSQL.

### IA

- Todas las llamadas a IA viven en backend.
- Nunca exponer API keys en frontend.
- Toda salida IA debe ser JSON estructurado.
- Toda salida IA debe validarse con Pydantic antes de guardarse.
- Nunca guardar como dato final una respuesta IA no validada.
- Mantener `model_version` y `prompt_version` en outputs relevantes.
- Las evaluaciones deben ser explicables, trazables y auditables.

---

## 6. Estructura esperada del repositorio

```text
talenscan/
  apps/
    web/
      app/
      components/
      components/ui/
      lib/
      hooks/
      types/
      styles/
      next.config.ts
      package.json
    api/
      app/
        main.py
        core/
          config.py
          security.py
          errors.py
        db/
          session.py
          base.py
        models/
        schemas/
        routers/
        services/
        ai/
        document_processing/
        scoring/
        pipeline/
        reporting/
        storage/
      alembic/
      tests/
      pyproject.toml
      Dockerfile
      fly.toml
  packages/
    shared-schemas/
      json-schemas/
      openapi/
  .devcontainer/
    devcontainer.json
  AGENTS.md
  README.md
  .env.example
  .gitignore
```

---

## 7. Terminología obligatoria de producto

Usar en la UI:

- Mandato de búsqueda.
- Perfil objetivo del cargo.
- Evaluación 360 Talenscan.
- Perfil estructurado del candidato.
- Pipeline de candidatos.
- Shortlist.
- Candidato.
- Calce.
- Score 360.
- Brecha crítica.
- Fortaleza.
- Debilidad.
- Riesgo a validar.
- Evidencia del CV.
- Preguntas sugeridas.
- Recomendación.
- Veredicto final.
- No evidenciado en el CV.
- Presentar al cliente.
- Mantener en reserva.
- Descartar candidato.
- Priorizar candidato.
- Descargar informe.
- Descargar Word.
- Descargar PDF.

Equivalencias internas permitidas:

| Concepto UI | Nombre técnico permitido |
|---|---|
| Mandato de búsqueda | SearchMandate |
| Perfil objetivo del cargo | PositionSpec |
| Perfil estructurado del candidato | CandidateProfile |
| Evaluación 360 Talenscan | CandidateEvaluation |
| Ítem del pipeline | CandidatePipelineItem |
| Brecha crítica | CriticalGap |

---

## 8. Estándar de lenguaje

La app debe hablar en español profesional, ejecutivo y claro.

Buenos ejemplos:

- Crear mandato de búsqueda.
- Generar perfil objetivo.
- Evaluar candidatos.
- Subir CV.
- Analizar candidato.
- Ver evaluación 360.
- Brechas críticas detectadas.
- No evidenciado en el CV.
- Avanzar a entrevista.
- Validar en entrevista.
- Mantener en reserva.
- Presentar al cliente.
- Descargar informe.
- Descargar Word.
- Descargar PDF.
- Mover a shortlist.
- Marcar como prioritario.
- Agregar nota del consultor.
- Ver evidencia.
- Revisar brechas.

Evitar textos en inglés visibles al usuario, tono juvenil, emojis, lenguaje robótico, lenguaje excesivamente técnico, “La IA cree que...”, “Probablemente...”, “Parece que...”, “Score mágico”, “Resultado generado automáticamente” sin explicación y mensajes genéricos de plantilla.

---

## 9. Dirección visual

El frontend debe verse como una app B2B premium, moderna y ejecutiva, similar en estándar visual a Qavante.

La UI debe sentirse moderna, minimalista, ejecutiva, limpia, premium, confiable, consultiva, rápida de entender y orientada a toma de decisiones.

No debe parecer dashboard genérico, admin template barato, demo técnica, Trello genérico, ATS antiguo, landing page de startup ni app sobrecargada.

### Paleta

- Azul principal: `#177FC6`.
- Gris claro: `#C7C6C6`.
- Gris medio: `#575756`.
- Negro casi absoluto: `#1D1D1B`.
- Fondo principal: `#F8FAFC`.
- Superficie: `#FFFFFF`.
- Bordes: `#E5E7EB`.

### Reglas visuales

- Light mode por defecto.
- Mucho espacio en blanco.
- Cards limpias.
- Bordes sutiles.
- Sombras suaves.
- Esquinas redondeadas.
- Tipografía moderna.
- Jerarquía visual clara.
- Azul usado con moderación.
- No usar gradientes pesados.
- No usar exceso de colores.
- No usar emojis.
- No mostrar JSON crudo al usuario.
- No mostrar logs técnicos al usuario.
- Cada pantalla debe parecer producto comercial real.

---

## 10. Navegación principal

Sidebar en español:

- Inicio.
- Mandatos.
- Pipeline.
- Candidatos.
- Evaluaciones.
- Reportes.
- Configuración.

Rutas iniciales:

```text
/
/mandatos
/mandatos/nuevo
/mandatos/[id]
/mandatos/[id]/perfil-objetivo
/mandatos/[id]/evaluar
/mandatos/[id]/pipeline
/candidatos
/candidatos/[id]
/evaluaciones
/evaluaciones/[id]
/reportes
/configuracion
```

En el detalle de un mandato, usar tabs:

- Resumen.
- Perfil objetivo.
- Candidatos.
- Pipeline.
- Evaluaciones.
- Reportes.

---

## 11. Componentes frontend obligatorios

### Layout

- AppShell.
- Sidebar.
- Topbar.
- PageHeader.

### Cards y datos

- MetricCard.
- DataCard.
- SearchMandateCard.
- CandidateSummaryCard.
- PositionSpecSection.

### Estados

- StatusBadge.
- CandidateStageBadge.
- EmptyState.
- StatusStepper.
- LoadingState.
- ErrorState.

### Formularios

- FormSection.
- PrimaryActionButton.
- SecondaryActionButton.
- UploadDropzone.

### Evaluación

- ScoreCard.
- ScoreDimensionTable.
- EvidenceBlock.
- RiskBlock.
- CriticalGapBlock.
- StrengthBlock.
- WeaknessBlock.
- InterviewQuestionsBlock.

### Pipeline

- CandidatePipelineBoard.
- PipelineColumn.
- CandidatePipelineCard.
- CandidateDragOverlay.
- PipelineFilters.
- CandidateQuickActions.
- ShortlistSummary.
- ConsultantNotesPopover.

### Reportes

- ReportDownloadButton.
- ReportFormatMenu.
- ReportGenerationStatus.

---

## 12. Dashboard inicial

Ruta: `/`

Nombre visible: `Inicio`

El dashboard debe mostrar valor inmediato, no una pantalla vacía.

Debe incluir métricas principales, acciones rápidas, últimos mandatos, últimas evaluaciones y shortlist reciente.

Métricas principales:

- Mandatos activos.
- CVs analizados.
- Candidatos preseleccionados.
- Score promedio.
- Informes generados.

Acciones rápidas:

- Crear mandato de búsqueda.
- Subir CV.
- Ver pipeline.
- Ver evaluaciones recientes.

---

## 13. Funcionalidad 1 — Mandato de búsqueda

Objetivo: permitir que el usuario levante un requerimiento de búsqueda de manera profesional y consultiva.

Pantalla: `Nuevo mandato de búsqueda`

Secciones del formulario:

1. Contexto del cliente.
2. Cargo requerido.
3. Contexto del negocio.
4. Responsabilidades.
5. Requisitos excluyentes.
6. Requisitos deseables.
7. Mercado objetivo.

Acciones:

- Guardar borrador.
- Crear mandato.
- Crear y generar perfil objetivo.

Estados del mandato:

- Borrador.
- Activo.
- Perfil objetivo generado.
- En evaluación de candidatos.
- Con shortlist.
- Cerrado.

Modelo `SearchMandate`:

```text
id
client_name
search_title
target_role
industry
country
city
work_mode
seniority_level
reports_to
business_context
role_objective
key_challenges
main_responsibilities
expected_results
must_have_requirements
nice_to_have_requirements
target_companies
target_industries
equivalent_roles
compensation_context
urgency
comments
status
created_at
updated_at
```

---

## 14. Funcionalidad 2 — Perfil objetivo del cargo

Objetivo: transformar el mandato en un perfil objetivo estructurado, profesional y evaluable.

Pantalla: `Perfil objetivo del cargo`

Acción: `Generar perfil objetivo`

El backend debe generar JSON estructurado y validado con Pydantic.

El perfil debe mostrar:

- Resumen ejecutivo del cargo.
- Misión del cargo.
- Contexto de la búsqueda.
- Responsabilidades principales.
- Resultados esperados.
- Requisitos excluyentes.
- Requisitos deseables.
- Competencias técnicas.
- Competencias funcionales.
- Competencias de liderazgo.
- Industrias objetivo.
- Tipos de empresas recomendadas.
- Cargos equivalentes.
- Hipótesis de mercado.
- Criterios de evaluación.
- Preguntas sugeridas para entrevista.
- Señales de alerta.
- Matriz de scoring.

Cada requisito debe tener estructura:

```json
{
  "requisito": "",
  "tipo": "excluyente | deseable | técnico | funcional | liderazgo | contextual",
  "fuente_validacion": "cv | entrevista | referencias | cv_y_entrevista | no_observable_directamente",
  "peso_evaluacion": 0,
  "preguntas_validacion": []
}
```

Regla crítica: el perfil objetivo no debe ser solo texto bonito. Debe ser una estructura evaluable, porque luego se usará para comparar candidatos.

Modelo `PositionSpec`:

```text
id
search_mandate_id
title
executive_summary
role_mission
search_context
key_responsibilities
expected_results
must_have_requirements
nice_to_have_requirements
technical_skills
functional_skills
leadership_skills
target_industries
target_company_types
equivalent_roles
market_mapping_hypothesis
evaluation_criteria
interview_questions
scoring_model
red_flags
validation_questions
generated_by_model
prompt_version
created_at
updated_at
```

---

## 15. Funcionalidad 3 — Carga y análisis de CV

Objetivo: permitir que el usuario suba CVs y que Talenscan los transforme en perfiles estructurados de candidatos.

Pantalla: `Evaluar candidatos`

Debe incluir selector del mandato, selector del perfil objetivo, UploadDropzone, lista de archivos cargados, estado de procesamiento, vista previa del candidato y acción “Generar evaluación 360”.

Formatos soportados: PDF, DOC y DOCX.

Reglas backend:

- Validar tipo de archivo.
- Validar tamaño máximo.
- Extraer texto.
- Guardar metadata del archivo.
- Guardar texto extraído.
- Si PDF no tiene texto suficiente, marcar como “requiere OCR”.
- Dejar hook preparado para OCR futuro.
- Manejar errores claramente.

Estados del documento:

- Recibido.
- Texto extraído.
- Requiere OCR.
- Error de extracción.
- Perfil del candidato generado.
- Evaluado.

Modelo `Candidate`:

```text
id
full_name
email
phone
linkedin_url
current_position
current_company
country
created_at
updated_at
```

Modelo `CandidateDocument`:

```text
id
candidate_id
file_name
file_type
file_size
file_url
raw_text
text_extraction_status
uploaded_at
```

---

## 16. Funcionalidad 4 — Perfil estructurado del candidato

Objetivo: transformar el texto del CV en un JSON estructurado, trazable y auditable.

`CandidateProfile` debe incluir candidate_name, current_position, current_company, total_years_experience, industries, roles, education, certifications, tools, languages, achievements, inferred_seniority, missing_information y evidence_snippets.

Cada rol debe incluir:

```json
{
  "title": "",
  "company": "",
  "start_date": "",
  "end_date": "",
  "duration_years": 0,
  "responsibilities": [],
  "achievements": [],
  "tools_or_systems": [],
  "evidence": []
}
```

Reglas críticas:

- No inventar información.
- Si algo no aparece en el CV, marcar “No evidenciado en el CV”.
- Guardar evidencia cuando sea posible.
- No inferir datos personales sensibles.
- No usar edad, género, estado civil, religión, dirección, foto, salud, nacionalidad o situación familiar para scoring.

Modelo `CandidateProfile`:

```text
id
candidate_id
candidate_document_id
current_position
current_company
total_years_experience
industries
roles
education
certifications
tools
languages
achievements
inferred_seniority
missing_information
evidence_snippets
parsed_json
created_at
```

---

## 17. Funcionalidad 5 — Evaluación 360 Talenscan

Objetivo: comparar el perfil estructurado del candidato contra el perfil objetivo del cargo.

Nombre visible: `Evaluación 360 Talenscan`

Debe generar score total de 0 a 100, categoría de calce, recomendación, resumen ejecutivo, score por dimensión, fortalezas, debilidades, brechas críticas, riesgos a validar, preguntas sugeridas, evidencia utilizada y veredicto final.

Dimensiones del scoring:

| Dimensión | Puntaje |
|---|---:|
| Requisitos excluyentes | 20 |
| Experiencia relevante | 15 |
| Calce industria / mercado | 10 |
| Seniority y nivel de responsabilidad | 10 |
| Competencias técnicas | 10 |
| Competencias funcionales | 10 |
| Logros e impacto demostrable | 10 |
| Formación y certificaciones | 5 |
| Trayectoria y estabilidad | 5 |
| Riesgos y brechas críticas | 5 |

Total máximo: 100 puntos.

Categorías visibles en español:

| Score | Categoría | Recomendación |
|---:|---|---|
| 85 a 100 | Muy alto calce | Priorizar entrevista |
| 70 a 84 | Buen calce | Avanzar a entrevista si las brechas son manejables |
| 55 a 69 | Calce parcial | Revisar brechas antes de avanzar |
| 40 a 54 | Bajo calce | Mantener en reserva, no priorizar |
| 0 a 39 | No recomendado | No avanzar para este mandato |

Reglas de scoring:

- El score debe ser explicable.
- El score no puede ser una nota mágica.
- Cada dimensión debe tener comentario, evidencia y nivel de evidencia.
- Si falta un requisito excluyente, debe marcarse como brecha crítica.
- Un candidato puede tener buen score general y aun así tener una brecha crítica.
- Las brechas críticas deben destacarse visualmente.
- No inventar información.
- No castigar por variables sensibles.
- No evaluar apariencia, edad, género, estado civil, fotografía, nacionalidad como factor discriminatorio, salud, dirección ni situación familiar.

Niveles de evidencia: Alta, Media, Baja, No evidenciado.

Objeto `DimensionScore`:

```json
{
  "dimension": "",
  "score": 0,
  "max_score": 0,
  "status": "",
  "evidence_level": "",
  "rationale": "",
  "supporting_evidence": []
}
```

Objeto `CriticalGap`:

```json
{
  "requirement": "",
  "reason": "",
  "impact": "",
  "evidence": "No evidenciado en el CV"
}
```

Modelo `CandidateEvaluation`:

```text
id
candidate_id
position_spec_id
total_score
score_category
recommendation
executive_summary
dimension_scores
critical_gaps
strengths
weaknesses
risks
interview_questions
supporting_evidence
final_verdict
evaluation_json
model_version
prompt_version
created_at
```

---

## 18. Pantalla de Evaluación 360

La pantalla “Evaluación 360 Talenscan” es una de las pantallas más importantes del MVP. Debe verse como una evaluación ejecutiva premium, no como una salida de IA.

Debe incluir encabezado, score principal, resumen ejecutivo, tabla de score por dimensión, fortalezas, debilidades, brechas críticas, riesgos a validar, preguntas sugeridas para entrevista y evidencia utilizada.

Acciones principales:

- Descargar informe Word.
- Descargar informe PDF.
- Mover a pipeline.
- Marcar como prioritario.
- Presentar al cliente.
- Mantener en reserva.
- Descartar.

---

## 19. Funcionalidad 6 — Pipeline interactivo tipo Kanban

Objetivo: permitir que el usuario gestione visualmente los candidatos asociados a un mandato, usando una interfaz tipo Kanban moderna, interactiva y premium.

Esta funcionalidad es parte del MVP.

Pantalla: `Pipeline de candidatos`

Ruta: `/mandatos/[id]/pipeline`

Debe permitir:

- Ver todos los candidatos asociados al mandato.
- Ver score 360.
- Ver categoría de calce.
- Ver estado del análisis.
- Ver brechas críticas.
- Mover candidatos entre columnas con drag & drop.
- Reordenar candidatos dentro de una columna.
- Abrir evaluación 360 desde la tarjeta.
- Marcar candidatos como prioritarios.
- Marcar candidatos como descartados.
- Agregar nota breve del consultor.
- Filtrar por score, estado, categoría de calce y brechas críticas.
- Buscar por nombre, cargo actual o empresa actual.
- Armar shortlist visual para presentar al cliente.
- Descargar informe desde la tarjeta.

Columnas iniciales:

1. CVs recibidos.
2. En análisis.
3. Evaluados.
4. Preseleccionados.
5. Entrevista.
6. En reserva.
7. Descartados.
8. Presentar al cliente.

Cada tarjeta debe mostrar nombre del candidato, cargo actual, empresa actual, score 360, categoría de calce, brechas críticas si existen, estado de evaluación, tags relevantes, última actualización y acciones rápidas.

Reglas UX:

- Drag & drop fluido.
- Usar dnd-kit.
- Optimistic UI.
- Persistir cambio en backend.
- Si falla backend, revertir movimiento y mostrar error claro.
- No perder orden manual definido por usuario.
- Soportar scroll horizontal y vertical por columna.
- Mostrar empty states por columna.
- Mostrar filtros superiores.
- Mantener experiencia premium tipo Qavante.
- No parecer Trello genérico.

Modelo `CandidatePipelineItem`:

```text
id
mandate_id
candidate_id
evaluation_id
stage
stage_order
is_priority
is_shortlisted
consultant_notes
discard_reason
tags
last_moved_at
created_at
updated_at
```

Valores permitidos `stage`:

```text
received
analyzing
evaluated
preselected
interview
reserve
discarded
present_to_client
```

Labels visibles:

| Stage | Label visible |
|---|---|
| received | CVs recibidos |
| analyzing | En análisis |
| evaluated | Evaluados |
| preselected | Preseleccionados |
| interview | Entrevista |
| reserve | En reserva |
| discarded | Descartados |
| present_to_client | Presentar al cliente |

---

## 20. Funcionalidad 7 — Informes Word y PDF

Objetivo: después de generar una Evaluación 360 Talenscan, el usuario debe poder descargar un informe profesional en Word y PDF.

Esta funcionalidad es parte del MVP.

Nombre visible: `Descargar informe`

Opciones:

- Descargar Word.
- Descargar PDF.

El informe debe ser profesional, ejecutivo y en español. Debe incluir nombre Talenscan, cliente, mandato, cargo evaluado, candidato, fecha, score 360, categoría de calce, recomendación, resumen ejecutivo, tabla por dimensión, fortalezas, debilidades, brechas críticas, riesgos, preguntas, evidencia y nota de trazabilidad.

Nota de trazabilidad sugerida:

```text
Informe generado por Talenscan a partir del perfil objetivo del cargo, el CV cargado y el modelo de evaluación configurado. La evaluación debe ser revisada por el consultor responsable antes de ser compartida con el cliente.
```

El informe no debe decir: Salida de IA, AI generated, Raw output ni Resultado automático sin revisión.

Diseño del informe: portada simple, títulos claros, tablas limpias, uso controlado del azul `#177FC6`, sin emojis, sin lenguaje técnico innecesario, sin raw JSON y formato ejecutivo.

Backend reporting:

Crear módulo:

```text
app/reporting/
```

Archivos sugeridos:

```text
report_context_builder.py
docx_report_generator.py
pdf_report_generator.py
templates/
  evaluation_report.html
  evaluation_report.css
  evaluation_report.docx
```

Reglas:

- El informe debe generarse desde datos guardados de evaluación.
- No hacer nueva llamada IA para generar informe.
- No recalcular score al generar informe.
- No modificar evaluación al generar informe.
- Si falta información, mostrar “No evidenciado en el CV”.
- PDF y Word deben tener el mismo contenido base.

Modelo opcional `CandidateEvaluationReport`:

```text
id
evaluation_id
report_type
file_name
file_url
generated_at
generated_by
created_at
```

---

## 21. Endpoints backend

### Health

```text
GET /health
```

### Mandatos

```text
POST /api/mandatos
GET /api/mandatos
GET /api/mandatos/{id}
PUT /api/mandatos/{id}
DELETE /api/mandatos/{id}
```

### Perfil objetivo

```text
POST /api/mandatos/{id}/generar-perfil-objetivo
GET /api/perfiles-objetivo/{id}
PUT /api/perfiles-objetivo/{id}
GET /api/mandatos/{id}/perfiles-objetivo
```

### Candidatos

```text
POST /api/candidatos
GET /api/candidatos
GET /api/candidatos/{id}
PUT /api/candidatos/{id}
```

### Documentos

```text
POST /api/candidatos/{id}/documentos
GET /api/candidatos/{id}/documentos
POST /api/documentos-candidato/{id}/generar-perfil
```

### Evaluaciones

```text
POST /api/evaluaciones
GET /api/evaluaciones
GET /api/evaluaciones/{id}
GET /api/perfiles-objetivo/{id}/evaluaciones
GET /api/candidatos/{id}/evaluaciones
```

### Pipeline

```text
GET /api/mandatos/{id}/pipeline
POST /api/mandatos/{id}/pipeline/items
PATCH /api/pipeline/items/{id}
PATCH /api/mandatos/{id}/pipeline/reorder
GET /api/mandatos/{id}/shortlist
```

### Reportes

```text
POST /api/evaluaciones/{id}/reportes/word
POST /api/evaluaciones/{id}/reportes/pdf
GET /api/reportes/{id}/download
```

---

## 22. Plan de ejecución por PRs

### PR 0 — Fundación técnica y visual

Crear monorepo, Next.js en `apps/web`, TypeScript, Tailwind, shadcn/ui, AppShell premium, Sidebar, Topbar, PageHeader, dashboard inicial, rutas placeholder en español, FastAPI en `apps/api`, `GET /health`, CORS, Pydantic Settings, devcontainer, README, AGENTS.md y `.env.example`.

Criterio de aceptación: frontend y backend levantan localmente, health responde OK, UI se ve como SaaS ejecutivo premium, app en español, dashboard no parece plantilla genérica y README explica cómo correr frontend y backend.

### PR 1 — Base de datos

Agregar persistencia PostgreSQL con SQLAlchemy, Alembic, modelos, migraciones, sesión DB y tests básicos.

### PR 2 — CRUD de mandatos

Crear, listar y editar mandatos. Implementar endpoints, service layer y UI en `/mandatos`, `/mandatos/nuevo`, `/mandatos/[id]`.

### PR 3 — Generador de perfil objetivo

Generar perfil objetivo estructurado desde mandato. Implementar `app/ai/position_spec_generator.py`, validación Pydantic, endpoint y vista ejecutiva.

### PR 4 — Carga y extracción de CV

Permitir subir CV, validar archivo, extraer PDF/DOCX, manejar DOC o error controlado y marcar OCR requerido si aplica.

### PR 5 — Perfil estructurado del candidato

Convertir CV en CandidateProfile JSON con `app/ai/candidate_profile_parser.py`, evidencia y “No evidenciado en el CV”.

### PR 6 — Motor de Evaluación 360

Comparar candidato contra perfil objetivo. Implementar `app/scoring/fit_score_engine.py`, `POST /api/evaluaciones`, score, dimensiones, brechas, evidencia y recomendación.

### PR 7 — UI ejecutiva de Evaluación 360

Crear pantalla premium `/evaluaciones/[id]` con ScoreCard, ScoreDimensionTable, CriticalGapBlock, EvidenceBlock, RiskBlock, preguntas, resumen y acciones.

### PR 8 — Pipeline interactivo Kanban con drag & drop

Crear `/mandatos/[id]/pipeline`, modelos y endpoints de pipeline, dnd-kit, optimistic UI, persistencia de etapa y orden, filtros y shortlist.

### PR 9 — Informes descargables Word y PDF

Crear módulo reporting, generar Word/PDF desde datos guardados, endpoints de descarga y UI con menú “Descargar informe”.

### PR 10 — Deploy

Preparar Dockerfile, fly.toml, variables, CORS, Cloudflare Pages, `NEXT_PUBLIC_API_BASE_URL` y build compatible.

### PR 11 — Seguridad, validación y QA

Auth simple o placeholder serio, validaciones, rate limit placeholder, estados de carga/error/empty, tests, logs, versionado de prompts/modelos, QA de pipeline, reportes y archivos inválidos.

---

## 23. Criterios de calidad 10/10

Para considerar el trabajo aceptable:

1. La app debe estar en español.
2. La UI debe verse moderna, limpia y premium.
3. El dashboard debe comunicar valor.
4. El mandato debe sentirse como levantamiento consultivo real.
5. El perfil objetivo debe ser evaluable, no solo texto.
6. El análisis de CV debe ser estructurado.
7. La evaluación 360 debe ser explicable.
8. Las brechas críticas deben ser visibles.
9. El pipeline debe ser interactivo y útil.
10. El drag & drop debe persistir cambios.
11. El informe Word/PDF debe parecer entregable profesional.
12. La arquitectura debe ser mantenible.
13. Las salidas IA deben ser validadas.
14. No debe haber secretos en frontend.
15. No debe haber textos visibles en inglés.
16. No debe haber pantallas genéricas.
17. No debe haber JSON crudo para usuario final.
18. No debe haber lenguaje de demo técnica.
19. El MVP debe poder presentarse comercialmente.
20. Cada pantalla debe empujar al usuario a la siguiente acción.

---

## 24. Primera tarea para Codex

Ejecutar solo PR 0.

Antes de escribir código:

1. Inspeccionar el repositorio.
2. Si está vacío, crear la estructura propuesta.
3. Listar los archivos que se van a crear.
4. Implementar solo PR 0.
5. No avanzar a PR 1 hasta que PR 0 esté completo.

Entregables PR 0:

- Monorepo.
- Frontend Next.js.
- Backend FastAPI.
- `GET /health`.
- AppShell premium.
- Dashboard inicial en español.
- Sidebar en español.
- Rutas placeholder en español.
- Devcontainer.
- README.
- AGENTS.md.
- `.env.example`.

Resultado esperado de PR 0:

Al abrir la app, Talenscan debe sentirse como el inicio de un producto SaaS ejecutivo real, moderno, premium y vendible.

No quiero una maqueta genérica.  
No quiero una demo técnica.  
No quiero una UI básica.  
No quiero una plantilla de administración.  
No quiero una app en inglés.

Quiero la base de un producto B2B serio, en español, con estándar visual tipo Qavante y orientado al flujo real de trabajo de un headhunter.
