"""App configuration.

Logic:
- Loads environment variables for DB + JWT + runtime environment.
- Keep configuration minimal and explicit for MVP.
"""

import os
import json
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


def _parse_cors_origins(raw_value: str) -> list[str]:
    value = (raw_value or "").strip()
    if not value:
        return ["http://localhost:3000", "http://localhost:5173", "http://localhost:4173"]

    if value == "*":
        return ["*"]

    if value.startswith("["):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass

    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "")
    jwt_secret: str = os.getenv("JWT_SECRET", "change_me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    env: str = os.getenv("ENV", "dev")

    redis_url: str = os.getenv("REDIS_URL", "")
    neo4j_uri: str = os.getenv("NEO4J_URI", "")
    vector_db_url: str = os.getenv("VECTOR_DB_URL", "")
    llm_api_base: str = os.getenv("LLM_API_BASE", "")

    ai_core_base_url: str = os.getenv("AI_CORE_BASE_URL", "")
    ai_core_timeout_seconds: float = float(os.getenv("AI_CORE_TIMEOUT_SECONDS", "8"))
    cors_origins: list[str] = _parse_cors_origins(os.getenv("CORS_ORIGINS", ""))

    internal_graph_base_url: str = os.getenv(
        "INTERNAL_GRAPH_BASE_URL", "http://127.0.0.1:8000/api/v1/internal/graph"
    )
    internal_graph_timeout_seconds: float = float(os.getenv("INTERNAL_GRAPH_TIMEOUT_SECONDS", "5"))
    internal_graph_max_retries: int = int(os.getenv("INTERNAL_GRAPH_MAX_RETRIES", "2"))


settings = Settings()
