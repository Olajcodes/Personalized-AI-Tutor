import os
import uuid

from sqlalchemy.orm import Session

from backend.core.database import SessionLocal
from backend.models.lesson import Lesson, LessonBlock
from backend.models.student import StudentProfile, StudentSubject
from backend.models.subject import Subject
from backend.models.topic import Topic


def run():
    db: Session = SessionLocal()
    try:
        def upsert_subject(slug: str, name: str) -> Subject:
            subject = db.query(Subject).filter(Subject.slug == slug).first()
            if subject:
                subject.name = name
                return subject

            subject = Subject(id=uuid.uuid4(), slug=slug, name=name)
            db.add(subject)
            db.flush()
            return subject

        def upsert_student_profile(student_id: uuid.UUID) -> StudentProfile:
            profile = db.query(StudentProfile).filter(StudentProfile.student_id == student_id).first()
            if profile:
                profile.sss_level = "SSS1"
                profile.active_term = 1
                return profile

            profile = StudentProfile(
                id=uuid.uuid4(),
                student_id=student_id,
                sss_level="SSS1",
                active_term=1,
            )
            db.add(profile)
            db.flush()
            return profile

        def ensure_student_subject(profile_id: uuid.UUID, subject_id: uuid.UUID) -> None:
            existing = db.query(StudentSubject).filter(
                StudentSubject.student_profile_id == profile_id,
                StudentSubject.subject_id == subject_id,
            ).first()
            if not existing:
                db.add(StudentSubject(id=uuid.uuid4(), student_profile_id=profile_id, subject_id=subject_id))

        math = upsert_subject("math", "Mathematics")
        eng = upsert_subject("english", "English")
        civic = upsert_subject("civic", "Civic Education")

        seed_student_id = uuid.UUID(os.getenv("SEED_STUDENT_ID", "00000000-0000-0000-0000-000000000001"))
        sp = upsert_student_profile(seed_student_id)

        for subj in (math, eng, civic):
            ensure_student_subject(sp.id, subj.id)

        def create_topic_lesson(subject: Subject, title: str) -> Topic:
            topic = db.query(Topic).filter(
                Topic.subject_id == subject.id,
                Topic.sss_level == "SSS1",
                Topic.term == 1,
                Topic.title == title,
            ).first()
            if not topic:
                topic = Topic(
                    id=uuid.uuid4(),
                    subject_id=subject.id,
                    sss_level="SSS1",
                    term=1,
                    title=title,
                    description="Sample seeded topic",
                    is_approved=True,
                )
                db.add(topic)
                db.flush()
            else:
                topic.description = "Sample seeded topic"
                topic.is_approved = True

            lesson = db.query(Lesson).filter(Lesson.topic_id == topic.id).first()
            if not lesson:
                lesson = Lesson(
                    id=uuid.uuid4(),
                    topic_id=topic.id,
                    title=f"Lesson: {title}",
                    summary="This is a seeded lesson to test content delivery.",
                    estimated_duration_minutes=15,
                )
                db.add(lesson)
                db.flush()
            else:
                lesson.title = f"Lesson: {title}"
                lesson.summary = "This is a seeded lesson to test content delivery."
                lesson.estimated_duration_minutes = 15

            db.query(LessonBlock).filter(LessonBlock.lesson_id == lesson.id).delete()
            db.add_all(
                [
                    LessonBlock(
                        id=uuid.uuid4(),
                        lesson_id=lesson.id,
                        block_type="text",
                        order_index=1,
                        content={"text": f"Introduction to {title} (seeded)."},
                    ),
                    LessonBlock(
                        id=uuid.uuid4(),
                        lesson_id=lesson.id,
                        block_type="example",
                        order_index=2,
                        content={"prompt": f"Example on {title}", "solution": "Seeded solution outline."},
                    ),
                    LessonBlock(
                        id=uuid.uuid4(),
                        lesson_id=lesson.id,
                        block_type="exercise",
                        order_index=3,
                        content={"question": "Try this yourself", "expected_answer": "Seeded expected answer."},
                    ),
                ]
            )
            return topic

        t1 = create_topic_lesson(math, "Linear Equations")
        t2 = create_topic_lesson(eng, "Parts of Speech")
        t3 = create_topic_lesson(civic, "Citizen and the Constitution")

        db.commit()

        print("Seed complete.")
        print(f"Test student_id: {seed_student_id}")
        print(f"Sample topic_ids: {t1.id}, {t2.id}, {t3.id}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
