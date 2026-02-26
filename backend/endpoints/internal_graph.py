from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from backend.schemas.internal_graph_schema import (
    InternalGraphContextOut,
    InternalGraphUpdateIn,
    InternalGraphUpdateOut
)
from backend.services.graph_client_service import graph_client_service

router = APIRouter(prefix="/internal/graph", tags=["Internal Graph APIs"])

@router.get("/context", response_model=InternalGraphContextOut)
def get_graph_context(
    student_id: UUID
):
    """
    GET /api/v1/internal/graph/context
    Retrieves the current knowledge graph state for a student.
    Used internally to inform AI tutoring and path generation.
    """
    context = graph_client_service.get_student_graph_context(student_id=student_id)
    if not context:
        raise HTTPException(status_code=404, detail="Graph context not found for student")
    return context

@router.post("/update-mastery", response_model=InternalGraphUpdateOut)
def update_graph_mastery(
    payload: InternalGraphUpdateIn
):
    """
    POST /api/v1/internal/graph/update-mastery
    Pushes mastery updates (from quizzes or diagnostics) into the Neo4j/Knowledge Graph.
    """
    try:
        return graph_client_service.push_mastery_update(payload=payload)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update knowledge graph: {str(e)}"
        )