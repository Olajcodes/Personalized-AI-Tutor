"""System health endpoints."""

from fastapi import APIRouter

from backend.services.system_health_service import SystemHealthService

router = APIRouter(prefix="/system", tags=["System"])

_health_service = SystemHealthService()


@router.get("/health")
def health():
    """Return deep health checks across core dependencies.

    Checks include active connectivity for Postgres, Redis, Neo4j, and Qdrant.
    LLM/API readiness is also reported based on configured ai-core/LLM settings.
    """
    return _health_service.snapshot()
