"""Internal RAG retrieval endpoint for AI orchestration services."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from backend.schemas.internal_rag_schema import InternalRagRetrieveRequest, InternalRagRetrieveResponse
from backend.services.rag_retrieve_service import RagRetrieveService, RagRetrieveServiceError

router = APIRouter(prefix="/internal/rag", tags=["Internal RAG APIs"])

_service = RagRetrieveService()


@router.post("/retrieve", response_model=InternalRagRetrieveResponse)
def retrieve_chunks(payload: InternalRagRetrieveRequest):
    """Retrieve scoped curriculum chunks for agentic tutor/quiz workflows.

    This API is intended for internal orchestration services, not direct frontend use.
    """
    try:
        return _service.retrieve(payload)
    except RagRetrieveServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
