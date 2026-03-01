"""Seed deterministic demo data across student, teacher, and admin flows.

Run:
  python -m backend.scripts.seed_demo_data
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from uuid import UUID, uuid5

from sqlalchemy.orm import Session

from backend.core.database import SessionLocal
from backend.core.security import hash_password
from backend.models.activity import ActivityLog, StudentStats
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
from backend.models.subject import Subject
from backend.models.teacher_assignment import TeacherAssignment
from backend.models.teacher_class import TeacherClass
from backend.models.teacher_intervention import TeacherIntervention
from backend.models.topic import Topic
from backend.models.tutor_message import TutorMessage
from backend.models.tutor_session import TutorSession
from backend.models.user import User


DEMO_NAMESPACE = UUID("8f10c1ca-20d6-4f46-81d5-c7e2204df349")


def _demo_uuid(name: str) -> UUID:
    return uuid5(DEMO_NAMESPACE, name)


DEMO_USER_PASSWORD = "DemoPass123!"

DEMO_IDS = {
    "admin_user": _demo_uuid("demo-admin-user"),
    "teacher_user": _demo_uuid("demo-teacher-user"),
    "student_user": _demo_uuid("demo-student-user"),
    "student_profile": _demo_uuid("demo-student-profile"),
    "teacher_class": _demo_uuid("demo-teacher-class"),
    "tutor_session": _demo_uuid("demo-tutor-session"),
    "quiz": _demo_uuid("demo-quiz"),
    "quiz_question_1": _demo_uuid("demo-quiz-question-1"),
    "quiz_question_2": _demo_uuid("demo-quiz-question-2"),
    "quiz_attempt": _demo_uuid("demo-quiz-attempt"),
    "quiz_answer_1": _demo_uuid("demo-quiz-answer-1"),
    "quiz_answer_2": _demo_uuid("demo-quiz-answer-2"),
    "mastery_snapshot": _demo_uuid("demo-mastery-snapshot"),
    "student_badge": _demo_uuid("demo-student-badge"),
    "curriculum_version": _demo_uuid("demo-curriculum-version"),
    "curriculum_ingestion_job": _demo_uuid("demo-curriculum-ingestion-job"),
    "curriculum_topic_map": _demo_uuid("demo-curriculum-topic-map"),
    "hallucination_flag": _demo_uuid("demo-hallucination-flag"),
}


def _upsert_subject(db: Session, slug: str, name: str) -> Subject:
    row = db.query(Subject).filter(Subject.slug == slug).first()
    if row is None:
        row = Subject(id=_demo_uuid(f"subject-{slug}"), slug=slug, name=name)
        db.add(row)
        db.flush()
    else:
        row.name = name
    return row


def _upsert_user(
    db: Session,
    *,
    user_id: UUID,
    email: str,
    role: str,
    first_name: str,
    last_name: str,
    display_name: str,
) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(
            id=user_id,
            email=email,
            password_hash=hash_password(DEMO_USER_PASSWORD),
            role=role,
            is_active=True,
            first_name=first_name,
            last_name=last_name,
            display_name=display_name,
        )
        db.add(user)
        db.flush()
        return user

    user.email = email
    user.role = role
    user.is_active = True
    user.first_name = first_name
    user.last_name = last_name
    user.display_name = display_name
    return user


def _upsert_topic_lesson(
    db: Session,
    *,
    subject: Subject,
    slug: str,
    title: str,
    sss_level: str,
    term: int,
) -> Topic:
    topic_id = _demo_uuid(f"topic-{slug}")
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if topic is None:
        topic = db.query(Topic).filter(
            Topic.subject_id == subject.id,
            Topic.sss_level == sss_level,
            Topic.term == term,
            Topic.title == title,
        ).first()
    if topic is None:
        topic = Topic(
            id=topic_id,
            subject_id=subject.id,
            sss_level=sss_level,
            term=term,
            title=title,
            description=f"Demo topic for {subject.slug}.",
            is_approved=True,
        )
        db.add(topic)
        db.flush()
    else:
        topic.subject_id = subject.id
        topic.sss_level = sss_level
        topic.term = term
        topic.title = title
        topic.description = f"Demo topic for {subject.slug}."
        topic.is_approved = True

    lesson_id = _demo_uuid(f"lesson-{slug}")
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if lesson is None:
        lesson = db.query(Lesson).filter(Lesson.topic_id == topic.id).first()
    if lesson is None:
        lesson = Lesson(
            id=lesson_id,
            topic_id=topic.id,
            title=f"{title} (Demo Lesson)",
            summary=f"Seeded lesson for {title}.",
            estimated_duration_minutes=15,
        )
        db.add(lesson)
        db.flush()
    else:
        lesson.topic_id = topic.id
        lesson.title = f"{title} (Demo Lesson)"
        lesson.summary = f"Seeded lesson for {title}."
        lesson.estimated_duration_minutes = 15

    db.query(LessonBlock).filter(LessonBlock.lesson_id == lesson.id).delete(synchronize_session=False)
    db.add_all(
        [
            LessonBlock(
                id=_demo_uuid(f"lesson-block-{slug}-1"),
                lesson_id=lesson.id,
                block_type="text",
                order_index=1,
                content={"text": f"Overview of {title}."},
            ),
            LessonBlock(
                id=_demo_uuid(f"lesson-block-{slug}-2"),
                lesson_id=lesson.id,
                block_type="example",
                order_index=2,
                content={"prompt": f"Worked example for {title}", "solution": "Step-by-step demo solution."},
            ),
            LessonBlock(
                id=_demo_uuid(f"lesson-block-{slug}-3"),
                lesson_id=lesson.id,
                block_type="exercise",
                order_index=3,
                content={"question": f"Practice question for {title}", "expected_answer": "Demo answer."},
            ),
        ]
    )
    return topic


def _ensure_student_profile(db: Session, *, student_user_id: UUID, subject_ids: list[UUID]) -> StudentProfile:
    profile = db.query(StudentProfile).filter(StudentProfile.student_id == student_user_id).first()
    if profile is None:
        profile = StudentProfile(
            id=DEMO_IDS["student_profile"],
            student_id=student_user_id,
            sss_level="SSS2",
            active_term=1,
        )
        db.add(profile)
        db.flush()
    else:
        profile.sss_level = "SSS2"
        profile.active_term = 1

    db.query(StudentSubject).filter(StudentSubject.student_profile_id == profile.id).delete(synchronize_session=False)
    for subject_id in subject_ids:
        db.add(
            StudentSubject(
                id=_demo_uuid(f"student-subject-{profile.id}-{subject_id}"),
                student_profile_id=profile.id,
                subject_id=subject_id,
            )
        )

    pref = db.query(LearningPreference).filter(LearningPreference.student_profile_id == profile.id).first()
    if pref is None:
        pref = LearningPreference(
            id=_demo_uuid("demo-learning-preference"),
            student_profile_id=profile.id,
            explanation_depth="standard",
            examples_first=True,
            pace="normal",
        )
        db.add(pref)
    else:
        pref.explanation_depth = "standard"
        pref.examples_first = True
        pref.pace = "normal"
    return profile


def _ensure_teacher_scope(
    db: Session,
    *,
    teacher_id: UUID,
    student_id: UUID,
) -> TeacherClass:
    teacher_class = db.query(TeacherClass).filter(TeacherClass.id == DEMO_IDS["teacher_class"]).first()
    if teacher_class is None:
        teacher_class = TeacherClass(
            id=DEMO_IDS["teacher_class"],
            teacher_id=teacher_id,
            name="Demo SSS2 Math Cohort",
            description="Seeded class for capstone demonstrations.",
            subject="math",
            sss_level="SSS2",
            term=1,
            is_active=True,
        )
        db.add(teacher_class)
        db.flush()
    else:
        teacher_class.teacher_id = teacher_id
        teacher_class.name = "Demo SSS2 Math Cohort"
        teacher_class.description = "Seeded class for capstone demonstrations."
        teacher_class.subject = "math"
        teacher_class.sss_level = "SSS2"
        teacher_class.term = 1
        teacher_class.is_active = True

    enrollment = db.query(ClassEnrollment).filter(
        ClassEnrollment.class_id == teacher_class.id,
        ClassEnrollment.student_id == student_id,
    ).first()
    if enrollment is None:
        enrollment = ClassEnrollment(
            id=_demo_uuid("demo-class-enrollment"),
            class_id=teacher_class.id,
            student_id=student_id,
            status="active",
        )
        db.add(enrollment)
    else:
        enrollment.status = "active"

    assignment = db.query(TeacherAssignment).filter(TeacherAssignment.id == _demo_uuid("demo-assignment")).first()
    if assignment is None:
        assignment = TeacherAssignment(
            id=_demo_uuid("demo-assignment"),
            teacher_id=teacher_id,
            class_id=teacher_class.id,
            student_id=student_id,
            assignment_type="topic",
            ref_id="demo-linear-equations",
            title="Linear Equations Drill",
            instructions="Solve questions 1-10 and review mistakes.",
            subject="math",
            sss_level="SSS2",
            term=1,
            status="assigned",
        )
        db.add(assignment)

    intervention = db.query(TeacherIntervention).filter(
        TeacherIntervention.id == _demo_uuid("demo-intervention")
    ).first()
    if intervention is None:
        intervention = TeacherIntervention(
            id=_demo_uuid("demo-intervention"),
            teacher_id=teacher_id,
            class_id=teacher_class.id,
            student_id=student_id,
            intervention_type="note",
            severity="medium",
            subject="math",
            sss_level="SSS2",
            term=1,
            notes="Student needs extra practice on equation balancing.",
            action_plan="Assign focused remediation and recheck in 48 hours.",
            status="open",
        )
        db.add(intervention)
    return teacher_class


def _ensure_student_activity_and_progress(db: Session, *, student_id: UUID, topic_id: UUID) -> None:
    existing = db.query(ActivityLog).filter(ActivityLog.ref_id == "demo-seed-activity").first()
    if existing is None:
        db.add_all(
            [
                ActivityLog(
                    id=_demo_uuid("demo-activity-lesson"),
                    student_id=student_id,
                    subject="math",
                    term=1,
                    event_type="lesson_viewed",
                    ref_id="demo-seed-activity",
                    duration_seconds=240,
                ),
                ActivityLog(
                    id=_demo_uuid("demo-activity-chat"),
                    student_id=student_id,
                    subject="math",
                    term=1,
                    event_type="tutor_chat",
                    ref_id="demo-seed-chat",
                    duration_seconds=180,
                ),
            ]
        )

    stats = db.query(StudentStats).filter(StudentStats.student_id == student_id).first()
    if stats is None:
        stats = StudentStats(
            student_id=student_id,
            current_streak=3,
            max_streak=5,
            total_mastery_points=180,
            total_study_time_seconds=4200,
            last_activity_date=date.today(),
        )
        db.add(stats)
    else:
        stats.current_streak = max(stats.current_streak, 3)
        stats.max_streak = max(stats.max_streak, 5)
        stats.total_mastery_points = max(stats.total_mastery_points, 180)
        stats.total_study_time_seconds = max(stats.total_study_time_seconds, 4200)
        stats.last_activity_date = date.today()

    snapshot = db.query(MasterySnapshot).filter(MasterySnapshot.id == DEMO_IDS["mastery_snapshot"]).first()
    payload = [{"concept_id": str(topic_id), "score": 0.72}]
    if snapshot is None:
        snapshot = MasterySnapshot(
            id=DEMO_IDS["mastery_snapshot"],
            student_id=student_id,
            subject="math",
            term=1,
            view="concept",
            snapshot_date=date.today(),
            mastery_payload=payload,
            overall_mastery=0.72,
            source="dashboard",
        )
        db.add(snapshot)
    else:
        snapshot.student_id = student_id
        snapshot.subject = "math"
        snapshot.term = 1
        snapshot.view = "concept"
        snapshot.snapshot_date = date.today()
        snapshot.mastery_payload = payload
        snapshot.overall_mastery = 0.72
        snapshot.source = "dashboard"

    badge = db.query(StudentBadge).filter(StudentBadge.id == DEMO_IDS["student_badge"]).first()
    if badge is None:
        badge = StudentBadge(
            id=DEMO_IDS["student_badge"],
            student_id=student_id,
            badge_code="CONSISTENCY_5",
            badge_name="Consistency 5",
            description="Maintained a 5-day activity streak.",
            metadata_payload={"source": "demo_seed"},
        )
        db.add(badge)
    else:
        badge.student_id = student_id
        badge.badge_code = "CONSISTENCY_5"
        badge.badge_name = "Consistency 5"
        badge.description = "Maintained a 5-day activity streak."
        badge.metadata_payload = {"source": "demo_seed"}


def _ensure_tutor_session(db: Session, *, student_id: UUID, topic_id: UUID) -> None:
    session = db.query(TutorSession).filter(TutorSession.id == DEMO_IDS["tutor_session"]).first()
    if session is None:
        session = TutorSession(
            id=DEMO_IDS["tutor_session"],
            student_id=student_id,
            subject="math",
            term=1,
            status="ended",
            duration_seconds=360,
            total_tokens=420,
            prompt_tokens=210,
            completion_tokens=210,
            cost_usd=0.021,
            end_reason="completed",
        )
        db.add(session)
        db.flush()
    else:
        session.student_id = student_id
        session.subject = "math"
        session.term = 1
        session.status = "ended"
        session.duration_seconds = 360
        session.total_tokens = 420
        session.prompt_tokens = 210
        session.completion_tokens = 210
        session.cost_usd = 0.021
        session.end_reason = "completed"

    db.query(TutorMessage).filter(TutorMessage.session_id == session.id).delete(synchronize_session=False)
    db.add_all(
        [
            TutorMessage(
                id=_demo_uuid("demo-tutor-message-student"),
                session_id=session.id,
                role="student",
                content=f"Please explain topic {topic_id} with examples.",
            ),
            TutorMessage(
                id=_demo_uuid("demo-tutor-message-assistant"),
                session_id=session.id,
                role="assistant",
                content="Start by isolating one variable, then solve step by step.",
            ),
        ]
    )


def _ensure_quiz_records(db: Session, *, student_id: UUID, topic_id: UUID) -> None:
    quiz = db.query(Quiz).filter(Quiz.id == DEMO_IDS["quiz"]).first()
    if quiz is None:
        quiz = Quiz(
            id=DEMO_IDS["quiz"],
            student_id=student_id,
            subject="math",
            sss_level="SSS2",
            term=1,
            topic_id=topic_id,
            purpose="practice",
            difficulty="medium",
            num_questions=2,
            status="submitted",
        )
        db.add(quiz)
        db.flush()
    else:
        quiz.student_id = student_id
        quiz.subject = "math"
        quiz.sss_level = "SSS2"
        quiz.term = 1
        quiz.topic_id = topic_id
        quiz.purpose = "practice"
        quiz.difficulty = "medium"
        quiz.num_questions = 2
        quiz.status = "submitted"

    db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).delete(synchronize_session=False)
    db.add_all(
        [
            QuizQuestion(
                id=DEMO_IDS["quiz_question_1"],
                quiz_id=quiz.id,
                question_number=1,
                question_text="Solve: 2x + 4 = 10",
                concept_id=str(topic_id),
                options=["x=1", "x=2", "x=3", "x=4"],
                correct_answer="x=3",
                explanation="Subtract 4 then divide by 2.",
            ),
            QuizQuestion(
                id=DEMO_IDS["quiz_question_2"],
                quiz_id=quiz.id,
                question_number=2,
                question_text="Solve: x - 5 = 7",
                concept_id=str(topic_id),
                options=["x=10", "x=11", "x=12", "x=13"],
                correct_answer="x=12",
                explanation="Add 5 to both sides.",
            ),
        ]
    )

    attempt = db.query(QuizAttempt).filter(QuizAttempt.id == DEMO_IDS["quiz_attempt"]).first()
    if attempt is None:
        attempt = QuizAttempt(
            id=DEMO_IDS["quiz_attempt"],
            quiz_id=quiz.id,
            student_id=student_id,
            time_taken_seconds=120,
            score=100,
            status="submitted",
            raw_answers=[
                {"question_id": str(DEMO_IDS["quiz_question_1"]), "answer": "x=3"},
                {"question_id": str(DEMO_IDS["quiz_question_2"]), "answer": "x=12"},
            ],
        )
        db.add(attempt)
        db.flush()
    else:
        attempt.quiz_id = quiz.id
        attempt.student_id = student_id
        attempt.time_taken_seconds = 120
        attempt.score = 100
        attempt.status = "submitted"
        attempt.raw_answers = [
            {"question_id": str(DEMO_IDS["quiz_question_1"]), "answer": "x=3"},
            {"question_id": str(DEMO_IDS["quiz_question_2"]), "answer": "x=12"},
        ]

    db.query(QuizAnswer).filter(QuizAnswer.attempt_id == attempt.id).delete(synchronize_session=False)
    db.add_all(
        [
            QuizAnswer(
                id=DEMO_IDS["quiz_answer_1"],
                attempt_id=attempt.id,
                question_id=DEMO_IDS["quiz_question_1"],
                selected_answer="x=3",
                is_correct=True,
                feedback="Correct.",
            ),
            QuizAnswer(
                id=DEMO_IDS["quiz_answer_2"],
                attempt_id=attempt.id,
                question_id=DEMO_IDS["quiz_question_2"],
                selected_answer="x=12",
                is_correct=True,
                feedback="Correct.",
            ),
        ]
    )


def _ensure_admin_scope(
    db: Session,
    *,
    admin_user_id: UUID,
    topic_id: UUID,
) -> None:
    source_root = str((Path("docs") / "SSS_NOTES_2026").resolve())
    version = db.query(CurriculumVersion).filter(CurriculumVersion.id == DEMO_IDS["curriculum_version"]).first()
    if version is None:
        version = CurriculumVersion(
            id=DEMO_IDS["curriculum_version"],
            version_name="demo-sss2-math-term1-v1",
            subject="math",
            sss_level="SSS2",
            term=1,
            source_root=source_root,
            source_file_count=1,
            status="published",
            metadata_payload={"source": "demo_seed"},
            uploaded_by=admin_user_id,
            approved_by=admin_user_id,
        )
        db.add(version)
        db.flush()
    else:
        version.version_name = "demo-sss2-math-term1-v1"
        version.subject = "math"
        version.sss_level = "SSS2"
        version.term = 1
        version.source_root = source_root
        version.source_file_count = 1
        version.status = "published"
        version.metadata_payload = {"source": "demo_seed"}
        version.uploaded_by = admin_user_id
        version.approved_by = admin_user_id

    ingestion = db.query(CurriculumIngestionJob).filter(
        CurriculumIngestionJob.id == DEMO_IDS["curriculum_ingestion_job"]
    ).first()
    if ingestion is None:
        ingestion = CurriculumIngestionJob(
            id=DEMO_IDS["curriculum_ingestion_job"],
            version_id=version.id,
            status="completed",
            progress_percent=100,
            current_stage="completed",
            processed_files_count=1,
            processed_chunks_count=3,
            logs_payload=[{"stage": "completed", "message": "Demo seed ingestion"}],
            created_by=admin_user_id,
        )
        db.add(ingestion)
    else:
        ingestion.version_id = version.id
        ingestion.status = "completed"
        ingestion.progress_percent = 100
        ingestion.current_stage = "completed"
        ingestion.processed_files_count = 1
        ingestion.processed_chunks_count = 3
        ingestion.logs_payload = [{"stage": "completed", "message": "Demo seed ingestion"}]
        ingestion.created_by = admin_user_id

    mapping = db.query(CurriculumTopicMap).filter(CurriculumTopicMap.id == DEMO_IDS["curriculum_topic_map"]).first()
    if mapping is None:
        mapping = CurriculumTopicMap(
            id=DEMO_IDS["curriculum_topic_map"],
            version_id=version.id,
            topic_id=topic_id,
            concept_id=str(topic_id),
            prereq_concept_ids=[],
            confidence=0.95,
            is_manual_override=True,
            created_by=admin_user_id,
        )
        db.add(mapping)
    else:
        mapping.version_id = version.id
        mapping.topic_id = topic_id
        mapping.concept_id = str(topic_id)
        mapping.prereq_concept_ids = []
        mapping.confidence = 0.95
        mapping.is_manual_override = True
        mapping.created_by = admin_user_id

    hall = db.query(GovernanceHallucination).filter(
        GovernanceHallucination.id == DEMO_IDS["hallucination_flag"]
    ).first()
    if hall is None:
        hall = GovernanceHallucination(
            id=DEMO_IDS["hallucination_flag"],
            student_id=DEMO_IDS["student_user"],
            session_id=DEMO_IDS["tutor_session"],
            endpoint="/api/v1/tutor/chat",
            reason_code="LOW_CONFIDENCE_CITATION",
            severity="low",
            status="open",
            prompt_excerpt="Explain linear equations.",
            response_excerpt="Draft response flagged for review.",
            citation_ids=[],
            evidence_payload={"source": "demo_seed"},
            reviewer_id=admin_user_id,
        )
        db.add(hall)
    else:
        hall.student_id = DEMO_IDS["student_user"]
        hall.session_id = DEMO_IDS["tutor_session"]
        hall.endpoint = "/api/v1/tutor/chat"
        hall.reason_code = "LOW_CONFIDENCE_CITATION"
        hall.severity = "low"
        hall.status = "open"
        hall.prompt_excerpt = "Explain linear equations."
        hall.response_excerpt = "Draft response flagged for review."
        hall.citation_ids = []
        hall.evidence_payload = {"source": "demo_seed"}
        hall.reviewer_id = admin_user_id


def run() -> None:
    db: Session = SessionLocal()
    try:
        # 1) Core users + subjects.
        admin_user = _upsert_user(
            db,
            user_id=DEMO_IDS["admin_user"],
            email="demo.admin@masteryai.local",
            role="admin",
            first_name="Admin",
            last_name="Demo",
            display_name="Demo Admin",
        )
        teacher_user = _upsert_user(
            db,
            user_id=DEMO_IDS["teacher_user"],
            email="demo.teacher@masteryai.local",
            role="teacher",
            first_name="Tunde",
            last_name="Adeyemi",
            display_name="Tunde Adeyemi",
        )
        student_user = _upsert_user(
            db,
            user_id=DEMO_IDS["student_user"],
            email="demo.student@masteryai.local",
            role="student",
            first_name="Olasquare",
            last_name="Adebayo",
            display_name="Olasquare Adebayo",
        )
        math = _upsert_subject(db, "math", "Mathematics")
        english = _upsert_subject(db, "english", "English")
        civic = _upsert_subject(db, "civic", "Civic Education")

        # 2) Curriculum scope + lessons.
        math_topic = _upsert_topic_lesson(
            db,
            subject=math,
            slug="math-linear-equations",
            title="Linear Equations",
            sss_level="SSS2",
            term=1,
        )
        _upsert_topic_lesson(
            db,
            subject=english,
            slug="english-concord",
            title="Concord",
            sss_level="SSS2",
            term=1,
        )
        _upsert_topic_lesson(
            db,
            subject=civic,
            slug="civic-rights-duties",
            title="Rights and Duties of Citizens",
            sss_level="SSS2",
            term=1,
        )

        # 3) Student setup + teacher setup.
        _ensure_student_profile(
            db,
            student_user_id=student_user.id,
            subject_ids=[math.id, english.id, civic.id],
        )
        _ensure_teacher_scope(db, teacher_id=teacher_user.id, student_id=student_user.id)

        # 4) Session/activity/quiz/mastery.
        _ensure_tutor_session(db, student_id=student_user.id, topic_id=math_topic.id)
        _ensure_student_activity_and_progress(db, student_id=student_user.id, topic_id=math_topic.id)
        _ensure_quiz_records(db, student_id=student_user.id, topic_id=math_topic.id)

        # 5) Admin/governance sample records.
        _ensure_admin_scope(db, admin_user_id=admin_user.id, topic_id=math_topic.id)

        db.commit()

        print("Demo seed complete.")
        print(f"Demo admin: {admin_user.email} / {DEMO_USER_PASSWORD} / id={admin_user.id}")
        print(f"Demo teacher: {teacher_user.email} / {DEMO_USER_PASSWORD} / id={teacher_user.id}")
        print(f"Demo student: {student_user.email} / {DEMO_USER_PASSWORD} / id={student_user.id}")
        print(f"Demo math topic_id: {math_topic.id}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
