import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.security import ApiKeyMiddleware
from app.routers.auth import router as auth_router
from app.routers.auth_oauth import router as auth_oauth_router
from app.routers.candidates import router as candidates_router
from app.routers.client_shortlists import router as client_shortlists_router
from app.routers.evaluations import router as evaluations_router
from app.routers.health import router as health_router
from app.routers.pipeline import router as pipeline_router
from app.routers.position_specs import router as position_specs_router
from app.routers.reports import router as reports_router
from app.routers.search_mandates import router as search_mandates_router
from app.routers.system import router as system_router
from app.routers.talent_market_maps import router as talent_market_maps_router
from app.routers.talent_profiles import router as talent_profiles_router

logger = logging.getLogger("talenscan")

app = FastAPI(title="Talenscan API", version="0.1.0")
# API key (interino) se agrega ANTES que CORS para que CORS quede como
# middleware externo y añada headers también a las respuestas 401.
app.add_middleware(ApiKeyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _log_runtime() -> None:
    logger.info(
        "Talenscan API arrancando · env=%s · api_key_auth=%s · openai=%s · apify=%s",
        settings.api_env,
        "on" if settings.api_key else "off",
        "on" if settings.openai_enabled else "off",
        "on" if settings.apify_enabled else "off",
    )
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(auth_oauth_router)
app.include_router(system_router)
app.include_router(search_mandates_router)
app.include_router(position_specs_router)
app.include_router(candidates_router)
app.include_router(evaluations_router)
app.include_router(pipeline_router)
app.include_router(reports_router)
app.include_router(client_shortlists_router)
app.include_router(talent_market_maps_router)
app.include_router(talent_profiles_router)
