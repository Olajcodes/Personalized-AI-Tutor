"""Seed realistic curriculum topics/lessons + demo learner data.

Usage:
  python -m backend.scripts.seed_lessons

Optional env:
  SEED_STUDENT_ID=<uuid>      # primary learner id used by frontend
  SEED_RESET=1                # clear existing topics/lessons/mastery before reseeding
"""

from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.core.database import SessionLocal
from backend.models.activity import StudentStats
from backend.models.lesson import Lesson, LessonBlock
from backend.models.student import StudentProfile, StudentSubject
from backend.models.student_concept_mastery import StudentConceptMastery
from backend.models.subject import Subject
from backend.models.topic import Topic
from backend.models.user import User

SEED_PASSWORD_HASH = "$2b$12$5JY6jsA5q9ODaW6fNfcohOx5l6v3PK2hQd1qi97V6S9bxR5D8Qqbi"
DOCS_ROOT = Path(__file__).resolve().parents[2] / "docs" / "SSS_NOTES_2026"
SUBJECT_SLUGS = ("math", "english", "civic")
SSS_LEVELS = ("SSS1", "SSS2", "SSS3")
TERMS = (1, 2, 3)
MIN_TOPICS_PER_SCOPE = 6
TRUTHY = {"1", "true", "yes", "on"}

BASE_SCOPE_TOPICS = {
    "math": {
        1: [
            "Sets and Operations",
            "Indices and Logarithms",
            "Quadratic Expressions",
            "Linear Inequalities",
            "Coordinate Geometry",
            "Variation and Proportion",
            "Mensuration of Solids",
        ],
        2: [
            "Trigonometric Ratios",
            "Sequences and Series",
            "Statistics and Data Representation",
            "Probability Basics",
            "Matrices and Determinants",
            "Bearings and Distances",
            "Circle Theorems",
        ],
        3: [
            "Differentiation Fundamentals",
            "Integration Fundamentals",
            "Financial Mathematics",
            "Plane Geometry Revision",
            "Transformation Geometry",
            "Logic and Mathematical Reasoning",
            "Applied Word Problems",
        ],
    },
    "english": {
        1: [
            "Sentence Structure and Clauses",
            "Parts of Speech in Context",
            "Comprehension Skills",
            "Lexis and Structure Practice",
            "Summary Writing Techniques",
            "Speech Work and Stress Patterns",
            "Formal Letter Writing",
        ],
        2: [
            "Essay Writing and Organization",
            "Reported and Direct Speech",
            "Concord and Agreement Rules",
            "Comprehension Inference Skills",
            "Oral English Practice",
            "Vocabulary Development",
            "Argumentative Writing",
        ],
        3: [
            "Advanced Grammar Editing",
            "Critical Reading and Evaluation",
            "Narrative Writing Craft",
            "Public Speaking and Delivery",
            "Summary and Precis Writing",
            "Exam Passage Strategy",
            "Language Register and Tone",
        ],
    },
    "civic": {
        1: [
            "Citizenship and National Values",
            "Rule of Law and Justice",
            "Human Rights and Responsibilities",
            "Constitutional Democracy",
            "Public Service and Integrity",
            "Community Development",
            "National Consciousness",
        ],
        2: [
            "Electoral Process and Participation",
            "Political Parties and Governance",
            "Consumer Rights and Duties",
            "Traffic Regulations and Public Safety",
            "Cultism and Drug Abuse Prevention",
            "Responsible Leadership",
            "Conflict Resolution",
        ],
        3: [
            "Democratic Institutions",
            "Corruption and National Development",
            "Peace and Conflict Management",
            "Human Trafficking Awareness",
            "Environmental Responsibility",
            "Global Citizenship",
            "Security Awareness",
        ],
    },
}


@dataclass(frozen=True)
class ScopeTopicCandidate:
    subject: str
    sss_level: str
    term: int
    title: str
    text: str
    source_file: str


@dataclass(frozen=True)
class SeedLearner:
    user_id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    display_name: str
    sss_level: str
    term: int
    streak: int
    best_streak: int
    points: int
    study_seconds: int


def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in TRUTHY


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _looks_like_heading(line: str) -> bool:
    compact = (line or "").strip()
    if len(compact) < 4 or len(compact) > 100:
        return False
    if compact.isupper() and len(compact.split()) <= 15:
        return True
    return bool(re.match(r"^(week|topic|unit|chapter|lesson)\b", compact, flags=re.IGNORECASE))


def _extract_sections(text: str) -> list[tuple[str, str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []

    sections: list[tuple[str, str]] = []
    current_heading = ""
    buffer: list[str] = []
    for line in lines:
        if _looks_like_heading(line) and buffer:
            sections.append((current_heading, " ".join(buffer)))
            current_heading = line
            buffer = [line]
            continue
        if _looks_like_heading(line):
            current_heading = line
        buffer.append(line)
    if buffer:
        sections.append((current_heading, " ".join(buffer)))
    return sections


def _clean_title(raw: str, fallback: str) -> str:
    candidate = re.sub(r"^(week|topic|unit|chapter|lesson)\s*\d*\s*[:.-]?\s*", "", raw or "", flags=re.IGNORECASE)
    candidate = re.sub(r"^[\d\W_]+", "", candidate)
    candidate = _normalize_space(candidate).strip(" -:\t")
    if len(candidate) < 4:
        candidate = fallback
    return candidate[:240]


def _read_docx(path: Path) -> str:
    from docx import Document

    try:
        doc = Document(str(path))
    except Exception:
        return ""
    paragraphs = [paragraph.text.strip() for paragraph in doc.paragraphs if paragraph.text and paragraph.text.strip()]
    return "\n".join(paragraphs)


def _infer_subject(text: str) -> str | None:
    value = text.upper()
    if re.search(r"\b(MATHEMATICS|MATHS|MATH)\b", value):
        return "math"
    if re.search(r"\bENGLISH\b", value):
        return "english"
    if re.search(r"\bCIVIC\b", value):
        return "civic"
    return None


def _infer_sss_level(text: str) -> str | None:
    value = text.upper()
    patterns = [r"\bSSS?\s*([123])\b", r"\bS([123])\b"]
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return f"SSS{match.group(1)}"
    return None


def _infer_term(text: str) -> int | None:
    value = text.upper()
    if "FIRST TERM" in value or "1ST TERM" in value or "TERM 1" in value:
        return 1
    if "SECOND TERM" in value or "2ND TERM" in value or "TERM 2" in value:
        return 2
    if "THIRD TERM" in value or "3RD TERM" in value or "TERM 3" in value:
        return 3
    return None


def _infer_scope(root: Path, file_path: Path) -> tuple[str, str, int] | None:
    try:
        relative = str(file_path.relative_to(root))
    except ValueError:
        relative = str(file_path)
    scope_hint = f"{relative} {file_path.stem}"
    subject = _infer_subject(scope_hint)
    sss_level = _infer_sss_level(scope_hint)
    term = _infer_term(scope_hint)
    if not subject or not sss_level or not term:
        return None
    return subject, sss_level, term


def _slice_words(text: str, max_words: int) -> str:
    words = _normalize_space(text).split()
    if not words:
        return ""
    return " ".join(words[:max_words])


def _candidate_text(topic_title: str, source_text: str, subject: str, sss_level: str, term: int) -> str:
    body = _slice_words(source_text, 180)
    if body:
        return body
    return (
        f"{topic_title} is part of {subject.upper()} for {sss_level} term {term}. "
        "Study the key principles, examples, and practice exercises in this lesson."
    )


def _build_doc_candidates(root: Path) -> list[ScopeTopicCandidate]:
    if not root.exists():
        return []

    candidates: list[ScopeTopicCandidate] = []
    used_titles_per_scope: dict[tuple[str, str, int], set[str]] = {}

    for file_path in sorted(root.rglob("*.docx")):
        scope = _infer_scope(root, file_path)
        if scope is None:
            continue
        subject, sss_level, term = scope
        raw_text = _read_docx(file_path)
        if not raw_text.strip():
            continue
        sections = _extract_sections(raw_text)[:12]
        if not sections:
            sections = [("", raw_text)]

        scope_key = (subject, sss_level, term)
        used_titles_per_scope.setdefault(scope_key, set())
        source_name = file_path.name
        fallback_prefix = _normalize_space(file_path.stem.title()) or "Curriculum Topic"

        for idx, (heading, section_text) in enumerate(sections):
            fallback_title = f"{fallback_prefix} Part {idx + 1}"
            title = _clean_title(heading, fallback_title)
            if not title:
                continue

            dedupe_title = title
            serial = 2
            while dedupe_title.lower() in used_titles_per_scope[scope_key]:
                dedupe_title = f"{title} ({serial})"
                serial += 1
            used_titles_per_scope[scope_key].add(dedupe_title.lower())

            candidates.append(
                ScopeTopicCandidate(
                    subject=subject,
                    sss_level=sss_level,
                    term=term,
                    title=dedupe_title[:240],
                    text=_candidate_text(dedupe_title, section_text, subject, sss_level, term),
                    source_file=source_name,
                )
            )

    return candidates


def _fallback_candidates(existing: Iterable[ScopeTopicCandidate]) -> list[ScopeTopicCandidate]:
    by_scope: dict[tuple[str, str, int], list[ScopeTopicCandidate]] = {}
    used_titles: dict[tuple[str, str, int], set[str]] = {}
    for item in existing:
        key = (item.subject, item.sss_level, item.term)
        by_scope.setdefault(key, []).append(item)
        used_titles.setdefault(key, set()).add(item.title.lower())

    additions: list[ScopeTopicCandidate] = []
    for subject in SUBJECT_SLUGS:
        for sss_level in SSS_LEVELS:
            for term in TERMS:
                key = (subject, sss_level, term)
                by_scope.setdefault(key, [])
                used_titles.setdefault(key, set())
                needed = max(0, MIN_TOPICS_PER_SCOPE - len(by_scope[key]))
                if needed == 0:
                    continue

                fallback_titles = BASE_SCOPE_TOPICS[subject][term]
                for title in fallback_titles:
                    if needed == 0:
                        break
                    if title.lower() in used_titles[key]:
                        continue
                    used_titles[key].add(title.lower())
                    needed -= 1
                    additions.append(
                        ScopeTopicCandidate(
                            subject=subject,
                            sss_level=sss_level,
                            term=term,
                            title=title,
                            text=(
                                f"{title} for {sss_level} term {term} in {subject.upper()} introduces the core ideas, "
                                "worked examples, and checkpoints needed for mastery progression."
                            ),
                            source_file="fallback",
                        )
                    )
    return additions


def _upsert_subject(db: Session, slug: str, name: str) -> Subject:
    row = db.query(Subject).filter(Subject.slug == slug).first()
    if row:
        row.name = name
        return row
    row = Subject(id=uuid.uuid4(), slug=slug, name=name)
    db.add(row)
    db.flush()
    return row


def _upsert_user(db: Session, learner: SeedLearner) -> User:
    user = db.query(User).filter(User.id == learner.user_id).first()
    if not user:
        user = db.query(User).filter(User.email == learner.email).first()
    if not user:
        user = User(id=learner.user_id, email=learner.email, password_hash=SEED_PASSWORD_HASH)
        db.add(user)
        db.flush()

    user.email = learner.email
    user.password_hash = user.password_hash or SEED_PASSWORD_HASH
    user.first_name = learner.first_name
    user.last_name = learner.last_name
    user.display_name = learner.display_name
    user.role = "student"
    user.is_active = True
    return user


def _upsert_profile(db: Session, *, user_id: uuid.UUID, sss_level: str, term: int) -> StudentProfile:
    row = db.query(StudentProfile).filter(StudentProfile.student_id == user_id).first()
    if row:
        row.sss_level = sss_level
        row.active_term = term
        return row
    row = StudentProfile(id=uuid.uuid4(), student_id=user_id, sss_level=sss_level, active_term=term)
    db.add(row)
    db.flush()
    return row


def _ensure_student_subject(db: Session, *, profile_id: uuid.UUID, subject_id: uuid.UUID) -> None:
    existing = db.query(StudentSubject).filter(
        StudentSubject.student_profile_id == profile_id,
        StudentSubject.subject_id == subject_id,
    ).first()
    if existing:
        return
    db.add(StudentSubject(id=uuid.uuid4(), student_profile_id=profile_id, subject_id=subject_id))


def _upsert_stats(db: Session, learner: SeedLearner) -> None:
    row = (
        db.query(StudentStats)
        .filter(StudentStats.student_id == learner.user_id)
        .first()
    )
    if row is None:
        row = StudentStats(
            student_id=learner.user_id,
            current_streak=0,
            max_streak=0,
            total_mastery_points=0,
            total_study_time_seconds=0,
        )
        db.add(row)
    row.current_streak = learner.streak
    row.max_streak = max(learner.best_streak, learner.streak)
    row.total_mastery_points = learner.points
    row.total_study_time_seconds = learner.study_seconds


def _generate_blocks(topic_title: str, topic_text: str) -> list[dict]:
    intro = _slice_words(topic_text, 160)
    if not intro:
        intro = f"This lesson introduces {topic_title} with definitions and practical examples."

    key_idea = _slice_words(topic_text, 40)
    if not key_idea:
        key_idea = f"The key idea in {topic_title} is to apply the governing rule consistently."

    return [
        {
            "block_type": "text",
            "order_index": 1,
            "content": {"text": intro},
        },
        {
            "block_type": "example",
            "order_index": 2,
            "content": {
                "prompt": f"Worked example on {topic_title}",
                "solution": (
                    f"Start with the core rule for {topic_title}, identify known values, "
                    "and show each step clearly before concluding."
                ),
                "note": key_idea,
            },
        },
        {
            "block_type": "exercise",
            "order_index": 3,
            "content": {
                "question": f"Practice task: apply {topic_title} to a new question and justify each step.",
                "expected_answer": "A clear step-by-step response that states the rule, applies it, and verifies the result.",
            },
        },
    ]


def _upsert_topic_and_lesson(
    db: Session,
    *,
    subject_id: uuid.UUID,
    candidate: ScopeTopicCandidate,
) -> tuple[Topic, bool]:
    topic = db.query(Topic).filter(
        Topic.subject_id == subject_id,
        Topic.sss_level == candidate.sss_level,
        Topic.term == candidate.term,
        Topic.title == candidate.title,
    ).first()
    created = False
    if topic is None:
        topic = Topic(
            id=uuid.uuid4(),
            subject_id=subject_id,
            sss_level=candidate.sss_level,
            term=candidate.term,
            title=candidate.title,
            description=_slice_words(candidate.text, 40),
            is_approved=True,
        )
        db.add(topic)
        db.flush()
        created = True
    else:
        topic.description = _slice_words(candidate.text, 40)
        topic.is_approved = True

    lesson = db.query(Lesson).filter(Lesson.topic_id == topic.id).first()
    if lesson is None:
        lesson = Lesson(
            id=uuid.uuid4(),
            topic_id=topic.id,
            title=f"Lesson: {candidate.title}",
            summary=_slice_words(candidate.text, 55),
            estimated_duration_minutes=15 + (len(candidate.text.split()) % 12),
        )
        db.add(lesson)
        db.flush()
    else:
        lesson.title = f"Lesson: {candidate.title}"
        lesson.summary = _slice_words(candidate.text, 55)
        lesson.estimated_duration_minutes = 15 + (len(candidate.text.split()) % 12)
        db.query(LessonBlock).filter(LessonBlock.lesson_id == lesson.id).delete(synchronize_session=False)

    for block in _generate_blocks(candidate.title, candidate.text):
        db.add(
            LessonBlock(
                id=uuid.uuid4(),
                lesson_id=lesson.id,
                block_type=block["block_type"],
                order_index=block["order_index"],
                content=block["content"],
            )
        )
    return topic, created


def _seed_mastery_for_scope(
    db: Session,
    *,
    student_id: uuid.UUID,
    subject: str,
    sss_level: str,
    term: int,
    topic_ids: list[uuid.UUID],
) -> None:
    db.query(StudentConceptMastery).filter(
        StudentConceptMastery.student_id == student_id,
        StudentConceptMastery.subject == subject,
        StudentConceptMastery.sss_level == sss_level,
        StudentConceptMastery.term == term,
    ).delete(synchronize_session=False)

    seed_pattern = [0.92, 0.84, 0.77, 0.69, 0.58, 0.46, 0.35, 0.28, 0.2]
    for index, topic_id in enumerate(topic_ids):
        score = seed_pattern[index] if index < len(seed_pattern) else max(0.08, 0.25 - (index * 0.02))
        db.add(
            StudentConceptMastery(
                id=uuid.uuid4(),
                student_id=student_id,
                subject=subject,
                sss_level=sss_level,
                term=term,
                concept_id=str(topic_id),
                mastery_score=score,
                source="seed_curriculum",
            )
        )


def run() -> None:
    db: Session = SessionLocal()
    try:
        # Avoid statement timeout cancellations on large seed runs.
        try:
            db.execute(text("SET statement_timeout TO 0"))
        except Exception:
            pass

        subject_map = {
            "math": _upsert_subject(db, "math", "Mathematics"),
            "english": _upsert_subject(db, "english", "English Language"),
            "civic": _upsert_subject(db, "civic", "Civic Education"),
        }

        seed_student_id = uuid.UUID(os.getenv("SEED_STUDENT_ID", "00000000-0000-0000-0000-000000000001"))
        learners = [
            SeedLearner(
                user_id=seed_student_id,
                email="olasquare.student@masteryai.local",
                first_name="Olasquare",
                last_name="Adeniyi",
                display_name="Olasquare",
                sss_level="SSS1",
                term=1,
                streak=9,
                best_streak=16,
                points=1260,
                study_seconds=41200,
            ),
            SeedLearner(
                user_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                email="amaka.student@masteryai.local",
                first_name="Amaka",
                last_name="Okonkwo",
                display_name="Amaka",
                sss_level="SSS2",
                term=2,
                streak=7,
                best_streak=13,
                points=1180,
                study_seconds=37500,
            ),
            SeedLearner(
                user_id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
                email="tunde.student@masteryai.local",
                first_name="Tunde",
                last_name="Afolabi",
                display_name="Tunde",
                sss_level="SSS3",
                term=1,
                streak=11,
                best_streak=19,
                points=1510,
                study_seconds=46900,
            ),
            SeedLearner(
                user_id=uuid.UUID("00000000-0000-0000-0000-000000000004"),
                email="zainab.student@masteryai.local",
                first_name="Zainab",
                last_name="Usman",
                display_name="Zainab",
                sss_level="SSS1",
                term=3,
                streak=5,
                best_streak=10,
                points=980,
                study_seconds=30400,
            ),
        ]

        for learner in learners:
            user = _upsert_user(db, learner)
            profile = _upsert_profile(db, user_id=user.id, sss_level=learner.sss_level, term=learner.term)
            _upsert_stats(db, learner)
            for subject in subject_map.values():
                _ensure_student_subject(db, profile_id=profile.id, subject_id=subject.id)
        db.commit()

        if _is_truthy(os.getenv("SEED_RESET")):
            db.query(LessonBlock).delete(synchronize_session=False)
            db.query(Lesson).delete(synchronize_session=False)
            db.query(Topic).delete(synchronize_session=False)
            db.query(StudentConceptMastery).delete(synchronize_session=False)
            db.commit()

        doc_candidates = _build_doc_candidates(DOCS_ROOT)
        candidates = doc_candidates + _fallback_candidates(doc_candidates)

        created_topics = 0
        updated_topics = 0
        scope_counter: dict[tuple[str, str, int], int] = {}
        topic_ids_by_scope: dict[tuple[str, str, int], list[uuid.UUID]] = {}

        for candidate in candidates:
            subject = subject_map[candidate.subject]
            topic, created = _upsert_topic_and_lesson(
                db,
                subject_id=subject.id,
                candidate=candidate,
            )
            if created:
                created_topics += 1
            else:
                updated_topics += 1

            scope_key = (candidate.subject, candidate.sss_level, candidate.term)
            scope_counter[scope_key] = scope_counter.get(scope_key, 0) + 1
            topic_ids_by_scope.setdefault(scope_key, []).append(topic.id)

        db.commit()

        for learner in learners:
            for subject in SUBJECT_SLUGS:
                scope_key = (subject, learner.sss_level, learner.term)
                topic_ids = topic_ids_by_scope.get(scope_key, [])[:9]
                _seed_mastery_for_scope(
                    db,
                    student_id=learner.user_id,
                    subject=subject,
                    sss_level=learner.sss_level,
                    term=learner.term,
                    topic_ids=topic_ids,
                )

        db.commit()

        print("Seed complete.")
        print(f"Primary student_id: {seed_student_id}")
        print(f"Topics created: {created_topics}")
        print(f"Topics updated: {updated_topics}")
        print(f"Scopes populated: {len(scope_counter)}")
        top_scopes = sorted(scope_counter.items(), key=lambda item: item[1], reverse=True)[:8]
        for (subject, sss_level, term), count in top_scopes:
            print(f"  - {subject} {sss_level} term {term}: {count} topics")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
