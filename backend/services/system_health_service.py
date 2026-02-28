"""Deep dependency health checks for system endpoint."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from backend.core.config import settings
from backend.core.database import engine
from backend.services.rag_retrieve_service import QdrantRuntimeConfig, QdrantVectorStore


class SystemHealthService:
    def _check_postgres(self) -> dict:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return {"status": "ok"}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    def _check_redis(self) -> dict:
        if not settings.redis_url:
            return {"status": "not_configured"}
        try:
            import redis
        except ModuleNotFoundError as exc:
            return {"status": "error", "detail": f"redis package missing: {exc}"}

        try:
            client = redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
            client.ping()
            return {"status": "ok"}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    def _check_neo4j(self) -> dict:
        if not (settings.neo4j_uri and settings.neo4j_user and settings.neo4j_password):
            return {"status": "not_configured"}
        try:
            from neo4j import GraphDatabase
        except ModuleNotFoundError as exc:
            return {"status": "error", "detail": f"neo4j package missing: {exc}"}

        try:
            driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
            driver.verify_connectivity()
            driver.close()
            return {"status": "ok"}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    def _check_vector_db(self) -> dict:
        if not settings.qdrant_url:
            return {"status": "not_configured"}
        store = QdrantVectorStore(
            QdrantRuntimeConfig(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key or None,
                collection=settings.qdrant_collection,
                embedding_model=settings.qdrant_embedding_model,
            )
        )
        return store.health()

    def _check_llm_api(self) -> dict:
        if settings.ai_core_base_url:
            try:
                response = httpx.get(
                    f"{settings.ai_core_base_url.rstrip('/')}/health",
                    timeout=settings.ai_core_timeout_seconds,
                )
                if response.status_code == 200:
                    return {"status": "ok"}
                return {"status": "error", "detail": f"ai-core health returned {response.status_code}"}
            except Exception as exc:
                return {"status": "error", "detail": str(exc)}
        if settings.llm_api_base:
            return {"status": "configured"}
        return {"status": "not_configured"}

    def snapshot(self) -> dict:
        checks = {
            "postgres": self._check_postgres(),
            "redis": self._check_redis(),
            "neo4j": self._check_neo4j(),
            "vector_db": self._check_vector_db(),
            "llm_api": self._check_llm_api(),
        }
        overall_status = "ok"
        if checks["postgres"]["status"] != "ok":
            overall_status = "degraded"
        elif any(item["status"] == "error" for item in checks.values()):
            overall_status = "degraded"

        return {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
        }
