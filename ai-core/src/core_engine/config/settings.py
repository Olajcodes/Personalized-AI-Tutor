"""Environment-driven settings for ai-core.

Keep all configuration here so the rest of the code stays clean and testable.
In FastAPI, import `get_settings()` once at startup and pass settings downstream.
"""

from __future__ import annotations
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    llm_model: str
    llm_api_key: str | None

    postgres_dsn: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    redis_url: str | None

    vector_store_provider: str
    vector_index_name: str
    embedding_model: str

    enable_basic_moderation: bool
    max_input_chars: int

    log_level: str
    cost_tracking_enabled: bool


def _bool(name: str, default: bool) -> bool:
    val = os.getenv(name, str(default)).strip().lower()
    return val in {"1", "true", "yes", "y", "on"}


def get_settings() -> Settings:
    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        llm_api_key=os.getenv("LLM_API_KEY"),
        postgres_dsn=os.getenv("POSTGRES_DSN", ""),
        neo4j_uri=os.getenv("NEO4J_URI", ""),
        neo4j_user=os.getenv("NEO4J_USER", ""),
        neo4j_password=os.getenv("NEO4J_PASSWORD", ""),
        redis_url=os.getenv("REDIS_URL"),
        vector_store_provider=os.getenv("VECTOR_STORE_PROVIDER", "faiss"),
        vector_index_name=os.getenv("VECTOR_INDEX_NAME", "jss_curriculum_v1"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        enable_basic_moderation=_bool("ENABLE_BASIC_MODERATION", True),
        max_input_chars=int(os.getenv("MAX_INPUT_CHARS", "6000")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        cost_tracking_enabled=_bool("COST_TRACKING_ENABLED", True),
    )
