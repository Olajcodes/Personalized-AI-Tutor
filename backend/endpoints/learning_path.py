from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.schemas.learning_path_schema import PathNextIn, PathNextOut
from backend.services.learning_path_service import learning_path_service

router = APIRouter(prefix="/learning/path", tags=["Learning Path"])

@router.post("/next", response_model=PathNextOut)
def get_next_path_step(
    payload: PathNextIn,
    db: Session = Depends(get_db)
):
    """
    POST /api/v1/learning/path/next
    Determines the next optimal topic or activity for the student.
    Returns topic recommendations and identifies prerequisite gaps.
    """
    try:
        return learning_path_service.calculate_next_step(db=db, payload=payload)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating next path step: {str(e)}"
        )