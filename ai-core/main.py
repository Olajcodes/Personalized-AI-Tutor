"""Lightweight ai-core HTTP app for container/service health."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import FastAPI

app = FastAPI(title="Mastery AI Core", version="0.1.0")


@app.get("/")
def root():
    return {"service": "ai-core", "status": "online"}


@app.get("/health")
def health():
    checks = {
        "llm_api_key": "configured" if os.getenv("LLM_API_KEY") else "not_configured",
        "postgres_dsn": "configured" if os.getenv("POSTGRES_DSN") else "not_configured",
        "neo4j_uri": "configured" if os.getenv("NEO4J_URI") else "not_configured",
        "redis_url": "configured" if os.getenv("REDIS_URL") else "not_configured",
        "vector_index_name": "configured" if os.getenv("VECTOR_INDEX_NAME") else "not_configured",
    }
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }
