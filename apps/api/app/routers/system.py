from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db

router = APIRouter(tags=["system"])


@router.get("/api/system/status")
def system_status(db: Session = Depends(get_db)) -> dict[str, object]:
    db_ok = False
    db_error: str | None = None
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as error:  # noqa: BLE001
        db_error = str(error)[:200]

    return {
        "service": "talenscan-api",
        "environment": settings.api_env,
        "database": {"ok": db_ok, "error": db_error},
        "openai": {
            "configured": settings.openai_enabled,
            "model": settings.openai_model if settings.openai_enabled else None,
        },
        "apify": {
            "configured": settings.apify_enabled,
            "actor": settings.apify_linkedin_actor if settings.apify_enabled else None,
        },
        "report_generation": {"pdf": True, "word": True},
    }
