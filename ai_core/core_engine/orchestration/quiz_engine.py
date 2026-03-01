"""AI Core Quiz Generation Engine.

Concept sourcing priority:
1) Curriculum topic maps for exact topic scope.
2) Curriculum topic maps for broader subject/level/term scope.
3) Deterministic fallback catalog when DB mappings are unavailable.
"""

from __future__ import annotations

import os
import random
import uuid
from typing import Any


_FALLBACK_CONCEPT_CATALOG: dict[str, list[str]] = {
    "math": [
        "algebraic-expressions",
        "linear-equations",
        "simultaneous-equations",
        "quadratic-equations",
        "statistics-basics",
        "probability",
    ],
    "english": [
        "parts-of-speech",
        "subject-verb-agreement",
        "comprehension-inference",
        "tense-consistency",
        "lexis-and-structure",
        "summary-writing",
    ],
    "civic": [
        "citizenship",
        "fundamental-human-rights",
        "rule-of-law",
        "arms-of-government",
        "democracy-and-elections",
        "national-values",
    ],
}


def _dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _load_postgres_repo(dsn: str):
    try:
        from ai_core.core_engine.integrations.postgres_repo import PostgresRepo
    except ModuleNotFoundError:
        from core_engine.integrations.postgres_repo import PostgresRepo  # pragma: no cover
    return PostgresRepo(dsn=dsn)


def _resolve_concept_pool(
    *,
    subject: str,
    sss_level: str,
    term: int,
    topic_id: uuid.UUID,
) -> list[str]:
    dsn = (os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL") or "").strip()
    if dsn:
        try:
            repo = _load_postgres_repo(dsn)
            scoped_topic = repo.list_scope_concepts(
                subject=subject,
                sss_level=sss_level,
                term=term,
                topic_id=str(topic_id),
                limit=250,
            )
            if scoped_topic:
                return _dedupe_keep_order(scoped_topic)

            scoped_subject = repo.list_scope_concepts(
                subject=subject,
                sss_level=sss_level,
                term=term,
                topic_id=None,
                limit=250,
            )
            if scoped_subject:
                return _dedupe_keep_order(scoped_subject)
        except Exception:
            # Keep quiz generation resilient when datastore is unavailable.
            pass

    fallback = _FALLBACK_CONCEPT_CATALOG.get(subject) or _FALLBACK_CONCEPT_CATALOG["math"]
    return _dedupe_keep_order(fallback)


def _letter_for_index(index: int) -> str:
    return ["A", "B", "C", "D"][index]


def _concept_label(concept: str) -> str:
    return (
        concept.replace("-", " ")
        .replace("_", " ")
        .replace("topic:", " ")
        .replace("concept:", " ")
        .strip()
    )


def _build_question_text(subject: str, concept: str, sss_level: str, term: int, idx: int) -> str:
    return (
        f"{subject.title()} ({sss_level} Term {term}) - Q{idx + 1}: "
        f"Which option best demonstrates understanding of {_concept_label(concept)}?"
    )


def _build_options(subject: str, concept: str) -> list[str]:
    concept_label = _concept_label(concept)
    return [
        f"A clear example of {concept_label} in {subject}",
        f"An unrelated fact from another topic",
        f"A partially correct but incomplete statement",
        f"A common misconception students make",
    ]


async def generate_quiz_questions(
    student_id: uuid.UUID | None,
    subject: str,
    sss_level: str,
    term: int,
    topic_id: uuid.UUID,
    purpose: str,
    difficulty: str,
    num_questions: int,
) -> list[dict[str, Any]]:
    seed = hash((str(student_id), subject, sss_level, term, str(topic_id), purpose, difficulty)) & 0xFFFFFFFF
    rng = random.Random(seed)

    concept_pool = _resolve_concept_pool(
        subject=subject,
        sss_level=sss_level,
        term=term,
        topic_id=topic_id,
    )
    if not concept_pool:
        concept_pool = [f"{subject}-core-concept"]
    shuffled_pool = concept_pool[:]
    rng.shuffle(shuffled_pool)

    questions: list[dict[str, Any]] = []
    for idx in range(num_questions):
        concept = shuffled_pool[idx % len(shuffled_pool)]
        options = _build_options(subject, concept)
        correct_index = rng.randint(0, 3)

        best_option = options[0]
        options[0], options[correct_index] = options[correct_index], best_option

        questions.append(
            {
                "id": uuid.uuid4(),
                "text": _build_question_text(subject, concept, sss_level, term, idx),
                "options": options,
                "correct_answer": _letter_for_index(correct_index),
                "concept_id": str(concept)[:255],
                "difficulty": difficulty,
            }
        )
    return questions


async def generate_quiz_insights(quiz_id: uuid.UUID, attempt_id: uuid.UUID) -> list[str]:
    seed = hash((str(quiz_id), str(attempt_id))) & 0xFFFFFFFF
    rng = random.Random(seed)
    suggestions = [
        "Revisit the lesson summary and attempt the missed concepts again.",
        "Practice slower: read each option fully before selecting an answer.",
        "Use the explanation mode to compare correct and incorrect choices.",
        "Schedule a 10-minute revision loop for weak concepts today.",
        "Focus on prerequisite ideas before attempting harder questions.",
    ]
    rng.shuffle(suggestions)
    return suggestions[:3]
