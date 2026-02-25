"""System endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from backend.core.config import settings
from backend.core.database import engine

router = APIRouter(prefix="/system", tags=["System"])


def _check_postgres() -> dict:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def _check_optional_config(value: str) -> dict:
    if value:
        return {"status": "configured"}
    return {"status": "not_configured"}


@router.get("/health")
def health():
    checks = {
        "postgres": _check_postgres(),
        "redis": _check_optional_config(settings.redis_url),
        "neo4j": _check_optional_config(settings.neo4j_uri),
        "vector_db": _check_optional_config(settings.vector_db_url),
        "llm_api": _check_optional_config(settings.llm_api_base),
    }

    overall_status = "ok" if checks["postgres"]["status"] == "ok" else "degraded"
    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }
