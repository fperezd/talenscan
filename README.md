# Talenscan - MVP en avance

Fundacion tecnica y visual + modulos funcionales iniciales del MVP de Talenscan.

## Stack

- Frontend: Next.js + TypeScript + Tailwind CSS
- Backend: FastAPI + Pydantic Settings
- Estructura: monorepo con workspaces npm

## Estructura

- `apps/web`: aplicacion frontend
- `apps/api`: aplicacion backend
- `.devcontainer`: entorno recomendado para desarrollo

## Requisitos

- Node.js 20+
- Python 3.11+

## Instalacion

```bash
npm install
python -m pip install fastapi uvicorn pydantic-settings sqlalchemy alembic psycopg[binary] python-docx pypdf python-multipart fpdf2 pytest httpx
```

## Ejecutar frontend

```bash
npm run dev:web
```

Frontend disponible en `http://localhost:3000`.

## Ejecutar backend

```bash
npm run dev:api
```

Backend disponible en `http://localhost:8000`.

## Healthcheck

```bash
curl http://localhost:8000/health
```

Respuesta esperada:

```json
{"status":"ok","service":"talenscan-api"}
```

## Deploy frontend en Cloudflare

Talenscan web queda desplegado como Worker con Static Assets.

PowerShell:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL="https://talenscan-api.fly.dev"
npm run build:web
npm run deploy:web:cf
```

URL publica actual:

`https://talenscan-web.tooxs-fperez.workers.dev`

## Migraciones (PR 1)

```bash
cd apps/api
alembic -c alembic.ini upgrade head
```

## Endpoints funcionales actuales

- Mandatos: CRUD completo
- Perfil objetivo: generar, listar, editar
- Candidatos: CRUD + carga de CV + perfil estructurado
- Evaluaciones: generar score 360 y consultar resultados
- Pipeline: tablero por mandato desde evaluaciones existentes
- Reportes: descarga Word y PDF por evaluacion

### Flujo rapido de prueba

1. Crear mandato: `POST /api/mandatos`
2. Generar perfil objetivo: `POST /api/mandatos/{id}/generar-perfil-objetivo`
3. Crear candidato: `POST /api/candidatos`
4. Subir CV: `POST /api/candidatos/{id}/documentos`
5. Generar perfil estructurado: `POST /api/documentos-candidato/{id}/generar-perfil`
6. Generar evaluacion 360: `POST /api/evaluaciones`
7. Descargar reporte Word: `POST /api/evaluaciones/{id}/reportes/word`
8. Descargar reporte PDF: `POST /api/evaluaciones/{id}/reportes/pdf`

## Variables de entorno

Usar `.env.example` como base para un archivo `.env` local.
