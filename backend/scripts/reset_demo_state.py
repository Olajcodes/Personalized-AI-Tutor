"""Delete deterministic demo seed data without touching non-demo records.

Run:
  python -m backend.scripts.reset_demo_state
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.core.database import SessionLocal
from backend.models.class_enrollment import ClassEnrollment
from backend.models.curriculum_ingestion_job import CurriculumIngestionJob
from backend.models.curriculum_topic_map import CurriculumTopicMap
from backend.models.curriculum_version import CurriculumVersion
from backend.models.governance_hallucination import GovernanceHallucination
from backend.models.lesson import Lesson, LessonBlock
from backend.models.mastery_snapshot import MasterySnapshot
from backend.models.quiz import Quiz
from backend.models.quiz_answer import QuizAnswer
from backend.models.quiz_attempt import QuizAttempt
from backend.models.quiz_question import QuizQuestion
from backend.models.student import LearningPreference, StudentProfile, StudentSubject
from backend.models.student_badge import StudentBadge
from backend.models.teacher_assignment import TeacherAssignment
from backend.models.teacher_class import TeacherClass
from backend.models.teacher_intervention import TeacherIntervention
from backend.models.topic import Topic
from backend.models.tutor_message import TutorMessage
from backend.models.tutor_session import TutorSession
from backend.models.user import User
from backend.scripts.seed_demo_data import DEMO_IDS, _demo_uuid


def run() -> None:
    db: Session = SessionLocal()
    try:
        student_id = DEMO_IDS["student_user"]
        teacher_id = DEMO_IDS["teacher_user"]
        admin_id = DEMO_IDS["admin_user"]
        class_id = DEMO_IDS["teacher_class"]
        session_id = DEMO_IDS["tutor_session"]
        quiz_id = DEMO_IDS["quiz"]
        version_id = DEMO_IDS["curriculum_version"]
        lesson_ids = [
            _demo_uuid("lesson-math-linear-equations"),
            _demo_uuid("lesson-english-concord"),
            _demo_uuid("lesson-civic-rights-duties"),
        ]
        topic_ids = [
            _demo_uuid("topic-math-linear-equations"),
            _demo_uuid("topic-english-concord"),
            _demo_uuid("topic-civic-rights-duties"),
        ]

        db.query(GovernanceHallucination).filter(
            GovernanceHallucination.id == DEMO_IDS["hallucination_flag"]
        ).delete(synchronize_session=False)
        db.query(CurriculumTopicMap).filter(
            CurriculumTopicMap.version_id == version_id
        ).delete(synchronize_session=False)
        db.query(CurriculumIngestionJob).filter(
            CurriculumIngestionJob.version_id == version_id
        ).delete(synchronize_session=False)
        db.query(CurriculumVersion).filter(
            CurriculumVersion.id == version_id
        ).delete(synchronize_session=False)

        db.query(QuizAnswer).filter(QuizAnswer.attempt_id == DEMO_IDS["quiz_attempt"]).delete(synchronize_session=False)
        db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz_id).delete(synchronize_session=False)
        db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).delete(synchronize_session=False)
        db.query(Quiz).filter(Quiz.id == quiz_id).delete(synchronize_session=False)

        db.query(TutorMessage).filter(TutorMessage.session_id == session_id).delete(synchronize_session=False)
        db.query(TutorSession).filter(TutorSession.id == session_id).delete(synchronize_session=False)

        db.query(TeacherIntervention).filter(TeacherIntervention.class_id == class_id).delete(synchronize_session=False)
        db.query(TeacherAssignment).filter(TeacherAssignment.class_id == class_id).delete(synchronize_session=False)
        db.query(ClassEnrollment).filter(ClassEnrollment.class_id == class_id).delete(synchronize_session=False)
        db.query(TeacherClass).filter(TeacherClass.id == class_id).delete(synchronize_session=False)

        db.query(StudentBadge).filter(StudentBadge.student_id == student_id).delete(synchronize_session=False)
        db.query(MasterySnapshot).filter(MasterySnapshot.student_id == student_id).delete(synchronize_session=False)
        db.query(StudentSubject).filter(
            StudentSubject.student_profile_id == DEMO_IDS["student_profile"]
        ).delete(synchronize_session=False)
        db.query(LearningPreference).filter(
            LearningPreference.student_profile_id == DEMO_IDS["student_profile"]
        ).delete(synchronize_session=False)
        db.query(StudentProfile).filter(
            StudentProfile.student_id == student_id
        ).delete(synchronize_session=False)

        db.query(LessonBlock).filter(LessonBlock.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
        db.query(Lesson).filter(Lesson.id.in_(lesson_ids)).delete(synchronize_session=False)
        db.query(Topic).filter(Topic.id.in_(topic_ids)).delete(synchronize_session=False)

        db.query(User).filter(User.id.in_([student_id, teacher_id, admin_id])).delete(synchronize_session=False)

        db.commit()
        print("Demo reset complete.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
