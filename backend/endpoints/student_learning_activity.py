# Importing all necessary libraries
from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.core.database import get_db

# I used two routers to adjust paths
# POST /learning/activity/log
# GET /students/stats
# GET /students/leaderboard

learning_router = APIRouter(prefix="/learning", tags=["Learning Activity"])
student_router = APIRouter(prefix="/students", tags=["Student Stats"])

# --- Pydantic Models ---
class ActivityLogCreate(BaseModel):
    student_id: UUID
    subject: str
    term: int
    event_type: str = Field(pattern="^(lesson_viewed|quiz_submitted|mastery_check_done|tutor_chat)$")
    ref_id: str
    duration_seconds: int

class StudentStats(BaseModel):
    streak: int
    mastery_points: int
    study_time_seconds: int

class LeaderboardEntry(BaseModel):
    student_id: UUID
    total_mastery_points: int
    rank: int


# --- API Endpoints ---

@learning_router.post("/activity/log", status_code=201)
def log_activity(activity: ActivityLogCreate, db: Session = Depends(get_db)):
    """
    POST /learning/activity/log
    Logs learning activity events used for streaks and analytics.
    """
    try:
        # Insert Raw Log
        insert_log_query = text("""
            INSERT INTO activity_logs (student_id, subject, term, event_type, ref_id, duration_seconds)
            VALUES (:sid, :subject, :term, :etype, :ref, :dur)
        """)
        
        # Points Logic & Stats Upsert
        points = 50 if activity.event_type == "quiz_submitted" else 10
        
        upsert_queries = text("""
            INSERT INTO daily_activity_summary (student_id, activity_date, total_duration, points_earned)
            VALUES (:sid, CURRENT_DATE, :dur, :points)
            ON CONFLICT (student_id, activity_date) DO UPDATE 
            SET total_duration = daily_activity_summary.total_duration + EXCLUDED.total_duration,
                points_earned = daily_activity_summary.points_earned + EXCLUDED.points_earned;

            INSERT INTO student_stats (student_id, total_mastery_points, total_study_time_seconds, last_activity_date)
            VALUES (:sid, :points, :dur, CURRENT_DATE)
            ON CONFLICT (student_id) DO UPDATE
            SET total_mastery_points = student_stats.total_mastery_points + EXCLUDED.total_mastery_points,
                total_study_time_seconds = student_stats.total_study_time_seconds + EXCLUDED.total_study_time_seconds,
                last_activity_date = EXCLUDED.last_activity_date,
                updated_at = CURRENT_TIMESTAMP;
        """)

        db.execute(insert_log_query, {
            "sid": activity.student_id, "subject": activity.subject, "term": activity.term,
            "etype": activity.event_type, "ref": activity.ref_id, "dur": activity.duration_seconds
        })
        
        db.execute(upsert_queries, {
            "sid": activity.student_id, "dur": activity.duration_seconds, "points": points
        })
        
        # Streak Logic
        db.execute(text("""
            UPDATE student_stats 
            SET current_streak = CASE 
                WHEN last_activity_date = CURRENT_DATE - INTERVAL '1 day' THEN current_streak + 1
                WHEN last_activity_date = CURRENT_DATE THEN current_streak
                ELSE 1
            END,
            max_streak = GREATEST(max_streak, current_streak)
            WHERE student_id = :sid
        """), {"sid": activity.student_id})

        db.commit()
        return {"status": "success", "message": "Activity logged"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@student_router.get("/stats", response_model=StudentStats)
def get_student_stats(student_id: UUID, db: Session = Depends(get_db)):
    """
    GET /students/stats
    KPI cards: streak, mastery points, study time.
    """
    query = text("""
        SELECT 
            COALESCE(current_streak, 0) as streak,
            COALESCE(total_mastery_points, 0) as mastery_points,
            COALESCE(total_study_time_seconds, 0) as study_time_seconds
        FROM student_stats
        WHERE student_id = :sid
    """)
    result = db.execute(query, {"sid": student_id}).fetchone()
    if not result:
        return {"streak": 0, "mastery_points": 0, "study_time_seconds": 0}
    return result

@student_router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(limit: int = 10, db: Session = Depends(get_db)):
    """
    GET /students/leaderboard
    Top students.
    """
    query = text("""
        SELECT 
            student_id,
            total_mastery_points,
            RANK() OVER (ORDER BY total_mastery_points DESC) as rank
        FROM student_stats
        ORDER BY total_mastery_points DESC
        LIMIT :limit
    """)
    return db.execute(query, {"limit": limit}).fetchall()