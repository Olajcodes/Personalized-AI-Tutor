import uuid
from sqlalchemy.orm import Session

from backend.core.database import SessionLocal
from backend.models.subject import Subject
from backend.models.student import StudentProfile, StudentSubject
from backend.models.topic import Topic
from backend.models.lesson import Lesson, LessonBlock

def run():
    db: Session = SessionLocal()
    try:
        # Subjects
        def upsert_subject(slug: str, name: str) -> Subject:
            s = db.query(Subject).filter(Subject.slug == slug).first()
            if s:
                return s
            s = Subject(id=uuid.uuid4(), slug=slug, name=name)
            db.add(s)
            db.flush()
            return s

        math = upsert_subject("math", "Mathematics")
        eng = upsert_subject("english", "English")
        civic = upsert_subject("civic", "Civic Education")

        # Create a sample student profile (for testing scope)
        student_id = uuid.uuid4()
        sp = StudentProfile(id=uuid.uuid4(), student_id=student_id, sss_level="SSS1", active_term=1)
        db.add(sp)
        db.flush()

        for subj in (math, eng, civic):
            db.add(StudentSubject(id=uuid.uuid4(), student_profile_id=sp.id, subject_id=subj.id))

        # One topic + lesson + blocks per subject
        def create_topic_lesson(subject: Subject, title: str):
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

            lesson = Lesson(
                id=uuid.uuid4(),
                topic_id=topic.id,
                title=f"Lesson: {title}",
                summary="This is a seeded lesson to test content delivery.",
                estimated_duration_minutes=15,
            )
            db.add(lesson)
            db.flush()

            blocks = [
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
            db.add_all(blocks)
            return topic

        t1 = create_topic_lesson(math, "Linear Equations")
        t2 = create_topic_lesson(eng, "Parts of Speech")
        t3 = create_topic_lesson(civic, "Citizen and the Constitution")

        db.commit()

        print("✅ Seed complete.")
        print(f"Test student_id: {student_id}")
        print(f"Sample topic_ids: {t1.id}, {t2.id}, {t3.id}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run()