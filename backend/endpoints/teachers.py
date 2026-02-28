"""Teacher intelligence endpoints.

Implements section-6 APIs for class management, analytics, and interventions.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.core.auth import get_current_user
from backend.core.database import get_db
from backend.repositories.teacher_repo import TeacherRepository
from backend.schemas.teacher_schema import (
    TeacherAlertsOut,
    TeacherAssignmentCreateIn,
    TeacherAssignmentOut,
    TeacherClassCreateIn,
    TeacherClassDashboardOut,
    TeacherClassEnrollIn,
    TeacherClassEnrollOut,
    TeacherClassHeatmapOut,
    TeacherClassListOut,
    TeacherClassOut,
    TeacherInterventionCreateIn,
    TeacherInterventionOut,
    TeacherStudentTimelineOut,
)
from backend.services.teacher_analytics_service import TeacherAnalyticsService
from backend.services.teacher_service import (
    TeacherService,
    TeacherServiceConflictError,
    TeacherServiceNotFoundError,
    TeacherServiceUnauthorizedError,
    TeacherServiceValidationError,
)

router = APIRouter(prefix="/teachers", tags=["Teacher Intelligence"])


def _teacher_service(db: Session) -> TeacherService:
    return TeacherService(TeacherRepository(db))


def _analytics_service(db: Session) -> TeacherAnalyticsService:
    return TeacherAnalyticsService(TeacherRepository(db))


@router.get("/classes", response_model=TeacherClassListOut)
def list_teacher_classes(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List classes owned by the authenticated teacher."""
    try:
        return _teacher_service(db).list_classes(teacher_id=current_user.id)
    except TeacherServiceUnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except TeacherServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/classes", response_model=TeacherClassOut, status_code=status.HTTP_201_CREATED)
def create_teacher_class(
    payload: TeacherClassCreateIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new class/cohort in a strict curriculum scope."""
    try:
        return _teacher_service(db).create_class(teacher_id=current_user.id, payload=payload)
    except TeacherServiceUnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except TeacherServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except TeacherServiceConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except TeacherServiceValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/classes/{class_id}/enroll", response_model=TeacherClassEnrollOut)
def enroll_students(
    class_id: UUID,
    payload: TeacherClassEnrollIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Enroll students into a teacher-owned class."""
    try:
        return _teacher_service(db).enroll_students(
            teacher_id=current_user.id,
            class_id=class_id,
            payload=payload,
        )
    except TeacherServiceUnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except TeacherServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except TeacherServiceValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/classes/{class_id}/enroll/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_student_enrollment(
    class_id: UUID,
    student_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Remove an active student enrollment from a class."""
    try:
        deleted = _teacher_service(db).remove_student_enrollment(
            teacher_id=current_user.id,
            class_id=class_id,
            student_id=student_id,
        )
    except TeacherServiceUnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except TeacherServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active enrollment not found for student in this class.",
        )
    return None


@router.get("/classes/{class_id}/dashboard", response_model=TeacherClassDashboardOut)
def class_dashboard(
    class_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return class-level KPI dashboard."""
    try:
        return _analytics_service(db).get_class_dashboard(teacher_id=current_user.id, class_id=class_id)
    except TeacherServiceUnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except TeacherServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/classes/{class_id}/heatmap", response_model=TeacherClassHeatmapOut)
def class_heatmap(
    class_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return concept-level class heatmap from mastery data."""
    try:
        return _analytics_service(db).get_class_heatmap(teacher_id=current_user.id, class_id=class_id)
    except TeacherServiceUnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except TeacherServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/classes/{class_id}/alerts", response_model=TeacherAlertsOut)
def class_alerts(
    class_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return inactivity/decline/prerequisite-failure alerts for class students."""
    try:
        return _analytics_service(db).get_class_alerts(teacher_id=current_user.id, class_id=class_id)
    except TeacherServiceUnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except TeacherServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/classes/{class_id}/students/{student_id}/timeline", response_model=TeacherStudentTimelineOut)
def student_timeline(
    class_id: UUID,
    student_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return detailed timeline for a student in a class."""
    try:
        return _analytics_service(db).get_student_timeline(
            teacher_id=current_user.id,
            class_id=class_id,
            student_id=student_id,
            limit=limit,
        )
    except TeacherServiceUnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except TeacherServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/assignments", response_model=TeacherAssignmentOut, status_code=status.HTTP_201_CREATED)
def create_assignment(
    payload: TeacherAssignmentCreateIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a teacher assignment for class or student targets."""
    try:
        return _teacher_service(db).create_assignment(teacher_id=current_user.id, payload=payload)
    except TeacherServiceUnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except TeacherServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except TeacherServiceValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/interventions", response_model=TeacherInterventionOut, status_code=status.HTTP_201_CREATED)
def create_intervention(
    payload: TeacherInterventionCreateIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create intervention notes/flags for at-risk students."""
    try:
        return _teacher_service(db).create_intervention(teacher_id=current_user.id, payload=payload)
    except TeacherServiceUnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except TeacherServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except TeacherServiceValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
