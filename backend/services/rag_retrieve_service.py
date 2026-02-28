"""Service for internal RAG retrieval against Qdrant."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from backend.core.config import settings
from backend.schemas.internal_rag_schema import (
    InternalRagChunkOut,
    InternalRagRetrieveRequest,
    InternalRagRetrieveResponse,
)


class RagRetrieveServiceError(RuntimeError):
    """Raised when retrieval from configured vector DB fails."""


@dataclass(frozen=True)
class QdrantRuntimeConfig:
    url: str
    api_key: str | None
    collection: str
    embedding_model: str

    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.collection and self.embedding_model)


class QdrantVectorStore:
    """Qdrant wrapper with embedding and payload-filtered retrieval."""

    def __init__(self, config: QdrantRuntimeConfig):
        self.config = config
        self._client = None
        self._embedder = None

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        try:
            from qdrant_client import QdrantClient
        except ModuleNotFoundError as exc:
            raise RagRetrieveServiceError(
                "qdrant-client is not installed. Add `qdrant-client` to backend dependencies."
            ) from exc

        self._client = QdrantClient(url=self.config.url, api_key=self.config.api_key)
        return self._client

    def _ensure_embedder(self):
        if self._embedder is not None:
            return self._embedder
        try:
            from fastembed import TextEmbedding
        except ModuleNotFoundError as exc:
            raise RagRetrieveServiceError(
                "fastembed is not installed. Add `fastembed` to backend dependencies."
            ) from exc

        self._embedder = TextEmbedding(model_name=self.config.embedding_model)
        return self._embedder

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        embedder = self._ensure_embedder()
        vectors = list(embedder.embed(texts))
        return [vector.tolist() for vector in vectors]

    def embed_query(self, query: str) -> list[float]:
        vectors = self._embed_texts([query])
        if not vectors:
            raise RagRetrieveServiceError("Embedding model returned no vector for query")
        return vectors[0]

    def ensure_collection(self, vector_size: int) -> None:
        client = self._ensure_client()
        try:
            exists = client.collection_exists(self.config.collection)
        except Exception as exc:  # pragma: no cover - defensive wrapper for qdrant API variants
            raise RagRetrieveServiceError(f"Failed to check Qdrant collection: {exc}") from exc

        if exists:
            return

        try:
            from qdrant_client.models import Distance, VectorParams

            client.create_collection(
                collection_name=self.config.collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
        except Exception as exc:
            raise RagRetrieveServiceError(f"Failed to create Qdrant collection: {exc}") from exc

    def upsert_chunks(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        client = self._ensure_client()
        vectors = self._embed_texts([str(row["text"]) for row in rows])
        if not vectors:
            raise RagRetrieveServiceError("Embedding model returned no vectors for chunk batch")
        self.ensure_collection(vector_size=len(vectors[0]))

        try:
            from qdrant_client.models import PointStruct

            points = [
                PointStruct(
                    id=str(row["id"]),
                    vector=vectors[idx],
                    payload=row["payload"],
                )
                for idx, row in enumerate(rows)
            ]
            client.upsert(collection_name=self.config.collection, points=points, wait=True)
        except Exception as exc:
            raise RagRetrieveServiceError(f"Failed to upsert chunks into Qdrant: {exc}") from exc

    def set_approval_flag(self, *, curriculum_version_id: UUID, approved: bool) -> None:
        client = self._ensure_client()
        try:
            from qdrant_client.models import FieldCondition, Filter, MatchValue

            selector = Filter(
                must=[
                    FieldCondition(
                        key="curriculum_version_id",
                        match=MatchValue(value=str(curriculum_version_id)),
                    )
                ]
            )
            client.set_payload(
                collection_name=self.config.collection,
                payload={"approved": approved},
                points=selector,
                wait=True,
            )
        except Exception as exc:
            raise RagRetrieveServiceError(f"Failed to update approval payload in Qdrant: {exc}") from exc

    def health(self) -> dict[str, Any]:
        client = self._ensure_client()
        try:
            collections = client.get_collections()
            names = {item.name for item in collections.collections}
            return {
                "status": "ok",
                "collection_exists": self.config.collection in names,
            }
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    def retrieve(self, payload: InternalRagRetrieveRequest) -> InternalRagRetrieveResponse:
        if not self.config.is_configured:
            raise RagRetrieveServiceError("Qdrant configuration is missing (url/collection/embedding model)")

        client = self._ensure_client()
        query_vector = self.embed_query(payload.query)

        try:
            from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

            must_conditions = [
                FieldCondition(key="subject", match=MatchValue(value=payload.subject)),
                FieldCondition(key="sss_level", match=MatchValue(value=payload.sss_level)),
                FieldCondition(key="term", match=MatchValue(value=payload.term)),
            ]
            if payload.approved_only:
                must_conditions.append(FieldCondition(key="approved", match=MatchValue(value=True)))
            if payload.curriculum_version_id is not None:
                must_conditions.append(
                    FieldCondition(
                        key="curriculum_version_id",
                        match=MatchValue(value=str(payload.curriculum_version_id)),
                    )
                )
            if payload.topic_ids:
                must_conditions.append(
                    FieldCondition(
                        key="topic_id",
                        match=MatchAny(any=[str(topic_id) for topic_id in payload.topic_ids]),
                    )
                )

            result = client.search(
                collection_name=self.config.collection,
                query_vector=query_vector,
                query_filter=Filter(must=must_conditions),
                limit=payload.top_k,
                with_payload=True,
            )
        except Exception as exc:
            raise RagRetrieveServiceError(f"Qdrant retrieval failed: {exc}") from exc

        chunks: list[InternalRagChunkOut] = []
        for item in result:
            metadata = dict(item.payload or {})
            chunks.append(
                InternalRagChunkOut(
                    chunk_id=str(metadata.get("chunk_id") or item.id),
                    source_id=str(metadata.get("source_id") or ""),
                    text=str(metadata.get("text") or ""),
                    score=float(item.score),
                    metadata=metadata,
                )
            )
        return InternalRagRetrieveResponse(chunks=chunks)


class RagRetrieveService:
    def __init__(self):
        self.store = QdrantVectorStore(
            QdrantRuntimeConfig(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key or None,
                collection=settings.qdrant_collection,
                embedding_model=settings.qdrant_embedding_model,
            )
        )

    def retrieve(self, payload: InternalRagRetrieveRequest) -> InternalRagRetrieveResponse:
        return self.store.retrieve(payload)
