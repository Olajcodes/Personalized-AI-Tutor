"""Qdrant-backed RAG retriever with strict scope filters."""

from __future__ import annotations

import json
import os
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


class RagRetrieverError(RuntimeError):
    pass


class RagRetriever:
    def __init__(
        self,
        repo: PostgresRepo,
        cache: Optional[RedisCache] = None,
        *,
        qdrant_url: str | None = None,
        qdrant_api_key: str | None = None,
        qdrant_collection: str | None = None,
        embedding_model: str | None = None,
    ):
        self.repo = repo
        self.cache = cache
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "")
        self.qdrant_api_key = qdrant_api_key or os.getenv("QDRANT_API_KEY", "")
        self.qdrant_collection = qdrant_collection or os.getenv("QDRANT_COLLECTION", "MasteryAI")
        self.embedding_model = embedding_model or os.getenv("QDRANT_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        self._client = None
        self._embedder = None

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        try:
            from qdrant_client import QdrantClient
        except ModuleNotFoundError as exc:
            raise RagRetrieverError("qdrant-client dependency missing in ai-core environment.") from exc

        if not self.qdrant_url:
            raise RagRetrieverError("QDRANT_URL is not configured for ai-core retriever.")
        self._client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key or None)
        return self._client

    def _ensure_embedder(self):
        if self._embedder is not None:
            return self._embedder
        try:
            from fastembed import TextEmbedding
        except ModuleNotFoundError as exc:
            raise RagRetrieverError("fastembed dependency missing in ai-core environment.") from exc

        self._embedder = TextEmbedding(model_name=self.embedding_model)
        return self._embedder

    def _embed_query(self, query: str) -> list[float]:
        embedder = self._ensure_embedder()
        vectors = list(embedder.embed([query]))
        if not vectors:
            raise RagRetrieverError("Embedding provider returned empty result for query.")
        return vectors[0].tolist()

    @staticmethod
    def _cache_key(
        *,
        query: str,
        subject_id: str,
        sss_level: str,
        term: int,
        allowed_topic_ids: list[str],
        approved_only: bool,
        top_k: int,
    ) -> str:
        payload = {
            "q": query,
            "subject_id": subject_id,
            "sss_level": sss_level,
            "term": term,
            "topic_ids": sorted(allowed_topic_ids),
            "approved_only": approved_only,
            "top_k": top_k,
        }
        return "rag:" + json.dumps(payload, sort_keys=True)

    def retrieve(
        self,
        *,
        query: str,
        subject_id: str,
        sss_level: str,
        term: int,
        allowed_topic_ids: List[str],
        approved_only: bool,
        top_k: int = 6,
    ) -> List[RagChunk]:
        if not query.strip() or not allowed_topic_ids:
            return []
        if not self.qdrant_url:
            # ai-core should degrade gracefully when vector DB is not configured.
            return []

        cache_key = self._cache_key(
            query=query,
            subject_id=subject_id,
            sss_level=sss_level,
            term=term,
            allowed_topic_ids=allowed_topic_ids,
            approved_only=approved_only,
            top_k=top_k,
        )
        if self.cache:
            cached = self.cache.get_json(cache_key)
            if isinstance(cached, list):
                return [RagChunk(**item) for item in cached]

        client = self._ensure_client()
        query_vector = self._embed_query(query)

        try:
            from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

            must_conditions = [
                FieldCondition(key="subject", match=MatchValue(value=subject_id)),
                FieldCondition(key="sss_level", match=MatchValue(value=sss_level)),
                FieldCondition(key="term", match=MatchValue(value=term)),
                FieldCondition(key="topic_id", match=MatchAny(any=list(allowed_topic_ids))),
            ]
            if approved_only:
                must_conditions.append(FieldCondition(key="approved", match=MatchValue(value=True)))

            response = client.search(
                collection_name=self.qdrant_collection,
                query_vector=query_vector,
                query_filter=Filter(must=must_conditions),
                with_payload=True,
                limit=top_k,
            )
        except Exception as exc:
            raise RagRetrieverError(f"Qdrant retrieval failed: {exc}") from exc

        chunks = []
        for item in response:
            payload = dict(item.payload or {})
            chunks.append(
                RagChunk(
                    chunk_id=str(payload.get("chunk_id") or item.id),
                    source_id=str(payload.get("source_id") or ""),
                    text=str(payload.get("text") or ""),
                    score=float(item.score),
                    metadata=payload,
                )
            )

        if self.cache:
            self.cache.set_json(cache_key, [chunk.__dict__ for chunk in chunks], ttl_seconds=300)
        return chunks
