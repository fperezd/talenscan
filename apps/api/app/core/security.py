"""Autenticación simple por API key compartida.

Middleware que exige el header `X-API-Key` en los endpoints de administración.
Se activa SÓLO si `settings.api_key` está configurada; si está vacía, no hace
nada (compatibilidad con el MVP sin auth).

Quedan SIEMPRE exentos:
- Vista pública del Decision Room (`/api/public/...`) — la protege su propio
  gate por código + sesión HMAC.
- Health checks y documentación.
- Preflight CORS (OPTIONS).
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

# Prefijos/paths exentos de API key.
_EXEMPT_PREFIXES = ("/api/public/",)
_EXEMPT_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json"}


def _is_exempt(path: str) -> bool:
    if path in _EXEMPT_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in _EXEMPT_PREFIXES)


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        configured = settings.api_key
        # Auth desactivada si no hay key configurada.
        if not configured:
            return await call_next(request)
        # Preflight CORS y endpoints exentos pasan sin key.
        if request.method == "OPTIONS" or _is_exempt(request.url.path):
            return await call_next(request)
        # Sólo protegemos la superficie /api (admin).
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        provided = request.headers.get("x-api-key") or _bearer(request)
        if provided != configured:
            return JSONResponse(
                status_code=401,
                content={"detail": "API key inválida o ausente."},
            )
        return await call_next(request)


def _bearer(request: Request) -> str | None:
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None
