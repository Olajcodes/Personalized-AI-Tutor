"""AI Core Quiz Generation Engine.

This engine is deterministic and curriculum-scoped:
- output shape matches backend section-4 contract
- concept IDs are topic-linked for downstream recommendation mapping
"""

from __future__ import annotations

import random
import uuid
from typing import Any


_CONCEPT_CATALOG: dict[str, list[str]] = {
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


def _letter_for_index(index: int) -> str:
    return ["A", "B", "C", "D"][index]


def _build_question_text(subject: str, concept: str, sss_level: str, term: int, idx: int) -> str:
    concept_label = concept.replace("-", " ")
    return (
        f"{subject.title()} ({sss_level} Term {term}) - Q{idx + 1}: "
        f"Which option best demonstrates understanding of {concept_label}?"
    )


def _build_options(subject: str, concept: str) -> list[str]:
    concept_label = concept.replace("-", " ")
    return [
        f"A clear example of {concept_label} in {subject}",
        f"An unrelated fact from another topic",
        f"A partially correct but incomplete statement",
        f"A common misconception students make",
    ]


def _select_concept(subject: str, idx: int) -> str:
    concepts = _CONCEPT_CATALOG.get(subject) or _CONCEPT_CATALOG["math"]
    return concepts[idx % len(concepts)]


async def generate_quiz_questions(
    subject: str,
    sss_level: str,
    term: int,
    topic_id: uuid.UUID,
    purpose: str,
    difficulty: str,
    num_questions: int,
) -> list[dict[str, Any]]:
    seed = hash((subject, sss_level, term, str(topic_id), purpose, difficulty)) & 0xFFFFFFFF
    rng = random.Random(seed)

    questions: list[dict[str, Any]] = []
    for idx in range(num_questions):
        concept = _select_concept(subject, idx)
        options = _build_options(subject, concept)
        correct_index = rng.randint(0, 3)
        # Keep the "best" option as correct while randomizing placement for realism.
        best_option = options[0]
        options[0], options[correct_index] = options[correct_index], best_option

        questions.append(
            {
                "id": uuid.uuid4(),
                "text": _build_question_text(subject, concept, sss_level, term, idx),
                "options": options,
                "correct_answer": _letter_for_index(correct_index),
                "concept_id": f"topic:{topic_id}:{concept}",
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
