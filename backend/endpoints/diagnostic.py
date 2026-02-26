from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.schemas.diagnostic_schema import (
    DiagnosticStartIn,
    DiagnosticStartOut,
    DiagnosticSubmitIn,
    DiagnosticSubmitOut
)
from backend.services.diagnostic_service import diagnostic_service

router = APIRouter(prefix="/learning/diagnostic", tags=["Learning Diagnostic"])

@router.post("/start", response_model=DiagnosticStartOut, status_code=status.HTTP_201_CREATED)
def start_diagnostic(
    payload: DiagnosticStartIn,
    db: Session = Depends(get_db)
):
    """
    POST /api/v1/learning/diagnostic/start
    Initializes a new diagnostic session for a student.
    Returns the diagnostic_id, concept_targets, and initial questions.
    """
    try:
        return diagnostic_service.create_diagnostic_session(db=db, payload=payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start diagnostic: {str(e)}"
        )

@router.post("/submit", response_model=DiagnosticSubmitOut)
def submit_diagnostic(
    payload: DiagnosticSubmitIn,
    db: Session = Depends(get_db)
):
    """
    POST /api/v1/learning/diagnostic/submit
    Submits diagnostic answers.
    Returns baseline mastery updates and the recommended starting topic.
    """
    try:
        return diagnostic_service.process_diagnostic_submission(db=db, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Submission error: {str(e)}"
        )