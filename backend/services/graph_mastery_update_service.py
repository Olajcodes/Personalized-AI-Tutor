from uuid import UUID
from datetime import datetime
from typing import List
import httpx  # for calling internal graph endpoint

from backend.schemas.quiz_schema import GraphMasteryUpdatePayload, ConceptBreakdownItem
from backend.core.config import settings

class GraphMasteryUpdateService:
    def __init__(self, db=None):  # db not strictly needed here
        self.db = db

    async def send_update(
        self,
        student_id: UUID,
        quiz_id: UUID,
        attempt_id: UUID,
        subject: str,
        sss_level: str,
        term: int,
        source: str,
        concept_breakdown: List[ConceptBreakdownItem]
    ):
        payload = GraphMasteryUpdatePayload(
            student_id=student_id,
            quiz_id=quiz_id,
            attempt_id=attempt_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
            timestamp=datetime.utcnow(),
            source=source,
            concept_breakdown=concept_breakdown
        )

        # Send to internal graph endpoint (e.g., POST /internal/graph/update-mastery)
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{settings.INTERNAL_GRAPH_BASE_URL}/update-mastery",
                    json=payload.dict(),
                    timeout=5.0
                )
                response.raise_for_status()
            except Exception as e:
                # Log error but don't break the flow – maybe queue for retry
                print(f"Graph update failed: {e}")
                # Optionally store in a dead-letter queue