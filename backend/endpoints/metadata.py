from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.core.database import get_db
from backend.models.subject import Subject

router = APIRouter(prefix="/metadata", tags=["Metadata"])

@router.get("/subjects")
def list_subjects(db: Session = Depends(get_db)):
    subjects = db.execute(select(Subject)).scalars().all()
    return [{"id": str(s.id), "slug": s.slug, "name": s.name} for s in subjects]