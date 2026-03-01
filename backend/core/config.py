"""App configuration.

Logic:
- Loads environment variables for DB + JWT + runtime environment.
- Keep configuration minimal and explicit for MVP.
"""

import os
import json
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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


def _parse_bool(raw_value: str | None, default: bool) -> bool:
    if raw_value is None:
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _normalize_database_url(raw_value: str) -> str:
    """Normalize database URL for known managed Postgres providers.

    Supabase pooler connections commonly require `sslmode=require`.
    This adds the query param when missing, while keeping other URLs unchanged.
    """
    value = (raw_value or "").strip()
    if not value:
        return value

    try:
        parsed = urlsplit(value)
    except ValueError:
        return value

    if not parsed.scheme.startswith("postgresql"):
        return value

    host = (parsed.hostname or "").lower()
    query_pairs = dict(parse_qsl(parsed.query, keep_blank_values=True))

    if "supabase.com" in host and "sslmode" not in query_pairs:
        query_pairs["sslmode"] = "require"
        return urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, urlencode(query_pairs), parsed.fragment)
        )

    return value


class Settings(BaseModel):
    database_url: str = _normalize_database_url(os.getenv("DATABASE_URL", ""))
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "5"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    db_pool_timeout_seconds: int = int(os.getenv("DB_POOL_TIMEOUT_SECONDS", "30"))
    db_pool_recycle_seconds: int = int(os.getenv("DB_POOL_RECYCLE_SECONDS", "300"))
    db_connect_timeout_seconds: int = int(os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "10"))
    db_keepalives_idle_seconds: int = int(os.getenv("DB_KEEPALIVES_IDLE_SECONDS", "30"))
    db_keepalives_interval_seconds: int = int(os.getenv("DB_KEEPALIVES_INTERVAL_SECONDS", "10"))
    db_keepalives_count: int = int(os.getenv("DB_KEEPALIVES_COUNT", "5"))
    jwt_secret: str = os.getenv("JWT_SECRET", "change_me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    env: str = os.getenv("ENV", "dev")

    redis_url: str = os.getenv("REDIS_URL", "")
    neo4j_uri: str = os.getenv("NEO4J_URI", "")
    neo4j_user: str = os.getenv("NEO4J_USER", "")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "")
    use_neo4j_graph: bool = _parse_bool(os.getenv("USE_NEO4J_GRAPH"), default=False)
    vector_db_url: str = os.getenv("VECTOR_DB_URL", "")
    qdrant_url: str = os.getenv("QDRANT_URL", os.getenv("VECTOR_DB_URL", ""))
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "MasteryAI")
    qdrant_embedding_model: str = os.getenv("QDRANT_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    llm_api_base: str = os.getenv("LLM_API_BASE", "")

    ai_core_base_url: str = os.getenv("AI_CORE_BASE_URL", "")
    ai_core_timeout_seconds: float = float(os.getenv("AI_CORE_TIMEOUT_SECONDS", "8"))
    ai_core_allow_fallback: bool = _parse_bool(os.getenv("AI_CORE_ALLOW_FALLBACK"), default=True)
    cors_origins: list[str] = _parse_cors_origins(os.getenv("CORS_ORIGINS", ""))

    internal_graph_base_url: str = os.getenv(
        "INTERNAL_GRAPH_BASE_URL", "http://127.0.0.1:8000/api/v1/internal/graph"
    )
    internal_graph_timeout_seconds: float = float(os.getenv("INTERNAL_GRAPH_TIMEOUT_SECONDS", "5"))
    internal_graph_max_retries: int = int(os.getenv("INTERNAL_GRAPH_MAX_RETRIES", "2"))


settings = Settings()
