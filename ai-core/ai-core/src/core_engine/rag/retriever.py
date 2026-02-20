"""Vector DB retrieval with strict metadata filters (MVP)."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core_engine.integrations.postgres_repo import PostgresRepo
from core_engine.integrations.redis_cache import RedisCache


@dataclass(frozen=True)
class RagChunk:
    chunk_id: str
    source_id: str
    text: str
    score: float
    metadata: Dict[str, Any]


class RagRetriever:
    def __init__(self, repo: PostgresRepo, cache: Optional[RedisCache] = None):
        self.repo = repo
        self.cache = cache

    def retrieve(
        self,
        *,
        query: str,
        subject_id: str,
        jss_level: str,
        term: int,
        allowed_topic_ids: List[str],
        approved_only: bool,
        top_k: int = 6,
    ) -> List[RagChunk]:
        """Retrieve chunks from vector store constrained by metadata filters.

        Replace this stub with:
- pgvector query OR pinecone/weaviate filtered search
- metadata filters: subject_id, jss_level, term, topic_id IN allowed_topic_ids, approved=true
        """
        return []
