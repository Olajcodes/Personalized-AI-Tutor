from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import re
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.repositories.diagnostic_repo import DiagnosticRepository
from backend.repositories.graph_repo import GraphRepository
from backend.schemas.diagnostic_schema import (
    BaselineMasteryUpdateOut,
    DiagnosticQuestionOut,
    DiagnosticStartIn,
    DiagnosticStartOut,
    DiagnosticSubmitIn,
    DiagnosticSubmitOut,
)
from backend.schemas.learning_path_schema import PathNextIn
from backend.services.learning_path_service import LearningPathValidationError, learning_path_service


MASTERY_PASS_THRESHOLD = 0.7


class DiagnosticValidationError(ValueError):
    pass


class DiagnosticNotFoundError(ValueError):
    pass


class DiagnosticAlreadySubmittedError(ValueError):
    pass


class DiagnosticService:
    @staticmethod
    def _readable_concept_label(concept_id: str, *, fallback_topic_title: str | None = None) -> str:
        value = str(concept_id or "").strip()
        if not value:
            return str(fallback_topic_title or "Untitled Concept").strip()
        token = value.rsplit(":", 1)[-1].strip().lower()
        token = re.sub(r"-(\d+)$", "", token)
        token = re.sub(r"[_-]+", " ", token)
        token = re.sub(r"\s+", " ", token).strip()
        return token.title() if token else str(fallback_topic_title or "Untitled Concept").strip()

    @staticmethod
    def _build_options(correct_title: str, other_titles: list[str]) -> list[str]:
        options = [correct_title]
        for title in other_titles:
            if title != correct_title and title not in options:
                options.append(title)
            if len(options) == 4:
                break
        while len(options) < 4:
            options.append(f"{correct_title} - variant {len(options)}")
        return options

    @staticmethod
    def _evaluate_answer(*, answer: str, question: dict) -> bool:
        normalized = answer.strip()
        correct_answer = str(question.get("correct_answer", "")).strip()
        if normalized.upper() == correct_answer.upper():
            return True

        options = question.get("options") or []
        if normalized in options and correct_answer.upper() in {"A", "B", "C", "D"}:
            idx = ord(correct_answer.upper()) - ord("A")
            if 0 <= idx < len(options):
                return normalized == options[idx]
        return False

    def create_diagnostic_session(self, db: Session, payload: DiagnosticStartIn) -> DiagnosticStartOut:
        repo = DiagnosticRepository(db)
        if not repo.validate_student_scope(
            student_id=payload.student_id,
            subject=payload.subject,
            sss_level=payload.sss_level,
            term=payload.term,
        ):
            raise DiagnosticValidationError(
                "Student scope is invalid. Ensure profile, level, term, and subject enrollment are correct."
            )

        topics = repo.get_scope_topics(
            subject=payload.subject,
            sss_level=payload.sss_level,
            term=payload.term,
        )
        if not topics:
            raise DiagnosticValidationError("No approved topics found for the requested scope.")

        concept_rows = repo.get_scope_topic_concept_rows(
            subject=payload.subject,
            sss_level=payload.sss_level,
            term=payload.term,
        )
        if not concept_rows:
            raise DiagnosticValidationError(
                "No curriculum concept mappings found for this scope. Ingest and approve mapped curriculum first."
            )

        topic_to_row: dict[str, dict] = {}
        concept_labels: list[str] = []
        for row in concept_rows:
            topic_id = str(row.get("topic_id") or "").strip()
            concept_id = str(row.get("concept_id") or "").strip()
            topic_title = str(row.get("topic_title") or "").strip()
            if not topic_id or not concept_id:
                continue
            if topic_id not in topic_to_row:
                topic_to_row[topic_id] = row
            label = self._readable_concept_label(concept_id, fallback_topic_title=topic_title)
            if label and label not in concept_labels:
                concept_labels.append(label)

        questions: list[dict] = []
        for topic in topics:
            row = topic_to_row.get(str(topic.id))
            if row is None:
                continue
            question_id = str(uuid4())
            concept_id = str(row["concept_id"])
            concept_label = self._readable_concept_label(concept_id, fallback_topic_title=str(topic.title))
            options = self._build_options(
                correct_title=concept_label,
                other_titles=concept_labels,
            )
            questions.append(
                {
                    "question_id": question_id,
                    "concept_id": concept_id,
                    "concept_label": concept_label,
                    "topic_id": str(topic.id),
                    "topic_title": str(topic.title),
                    "prompt": f"For the topic '{topic.title}', which concept should you recognise first?",
                    "options": options,
                    "correct_answer": "A",
                }
            )
        if not questions:
            raise DiagnosticValidationError(
                "No mapped concepts are available to build a diagnostic for this scope yet."
            )

        concept_targets = [q["concept_id"] for q in questions]

        diagnostic = repo.create_diagnostic(
            student_id=payload.student_id,
            subject=payload.subject,
            sss_level=payload.sss_level,
            term=payload.term,
            concept_targets=concept_targets,
            questions=questions,
        )
        db.commit()
        db.refresh(diagnostic)

        return DiagnosticStartOut(
            diagnostic_id=diagnostic.id,
            concept_targets=concept_targets,
            questions=[
                DiagnosticQuestionOut(
                    question_id=q["question_id"],
                    concept_id=q["concept_id"],
                    concept_label=q.get("concept_label"),
                    topic_id=q.get("topic_id"),
                    topic_title=q.get("topic_title"),
                    prompt=q["prompt"],
                    options=q["options"],
                )
                for q in questions
            ],
        )

    def process_diagnostic_submission(self, db: Session, payload: DiagnosticSubmitIn) -> DiagnosticSubmitOut:
        repo = DiagnosticRepository(db)
        graph_repo = GraphRepository(db)

        diagnostic = repo.get_diagnostic(
            diagnostic_id=payload.diagnostic_id,
            student_id=payload.student_id,
        )
        if not diagnostic:
            raise DiagnosticNotFoundError("Diagnostic session not found for this student.")
        if diagnostic.status == "submitted":
            raise DiagnosticAlreadySubmittedError("Diagnostic session has already been submitted.")

        questions = diagnostic.questions or []
        if not questions:
            raise DiagnosticValidationError("Diagnostic has no question set.")

        expected_by_id = {str(q["question_id"]): q for q in questions if "question_id" in q}
        if not expected_by_id:
            raise DiagnosticValidationError("Diagnostic questions are malformed.")

        submitted_by_id = {str(a.question_id): a for a in payload.answers}
        missing = [qid for qid in expected_by_id.keys() if qid not in submitted_by_id]
        if missing:
            raise DiagnosticValidationError("Submission must include all diagnostic questions.")

        concept_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})
        graded_answers: list[dict] = []
        correct_count = 0

        for question_id, question in expected_by_id.items():
            submitted = submitted_by_id.get(question_id)
            if submitted is None:
                continue

            is_correct = self._evaluate_answer(answer=submitted.answer, question=question)
            concept_id = str(question["concept_id"])
            concept_stats[concept_id]["total"] += 1
            if is_correct:
                concept_stats[concept_id]["correct"] += 1
                correct_count += 1

            graded_answers.append(
                {
                    "question_id": question_id,
                    "answer": submitted.answer,
                    "is_correct": is_correct,
                    "concept_id": concept_id,
                }
            )

        existing_mastery = graph_repo.get_mastery_map(
            student_id=payload.student_id,
            subject=diagnostic.subject,
            sss_level=diagnostic.sss_level,
            term=diagnostic.term,
        )

        baseline_updates: list[BaselineMasteryUpdateOut] = []
        for concept_id in diagnostic.concept_targets:
            stats = concept_stats.get(concept_id, {"correct": 0, "total": 0})
            accuracy = (stats["correct"] / stats["total"]) if stats["total"] > 0 else 0.0

            previous = existing_mastery.get(concept_id, 0.0)
            projected = max(0.0, min(1.0, round((previous * 0.35) + (accuracy * 0.65), 4)))
            stored_previous, stored_new = graph_repo.upsert_mastery(
                student_id=payload.student_id,
                subject=diagnostic.subject,
                sss_level=diagnostic.sss_level,
                term=diagnostic.term,
                concept_id=concept_id,
                new_score=projected,
                source="diagnostic",
                evaluated_at=datetime.now(timezone.utc),
            )
            existing_mastery[concept_id] = stored_new
            baseline_updates.append(
                BaselineMasteryUpdateOut(
                    concept_id=concept_id,
                    previous_score=round(stored_previous, 4),
                    new_score=round(stored_new, 4),
                    delta=round(stored_new - stored_previous, 4),
                )
            )

        topics = repo.get_scope_topics(
            subject=diagnostic.subject,
            sss_level=diagnostic.sss_level,
            term=diagnostic.term,
        )
        recommended_start_topic_id: str | None = None
        recommended_start_topic_title: str | None = None
        scope_warning: str | None = None
        if topics:
            try:
                next_step = learning_path_service.calculate_next_step(
                    db=db,
                    payload=PathNextIn(
                        student_id=payload.student_id,
                        subject=diagnostic.subject,  # type: ignore[arg-type]
                        sss_level=diagnostic.sss_level,  # type: ignore[arg-type]
                        term=diagnostic.term,
                    ),
                )
                recommended_start_topic_id = next_step.recommended_topic_id
                recommended_start_topic_title = next_step.recommended_topic_title
                scope_warning = next_step.scope_warning
            except LearningPathValidationError:
                recommended_start_topic_id = None

        total_questions = len(expected_by_id)
        score = round((correct_count / total_questions) * 100.0, 2) if total_questions > 0 else 0.0

        repo.save_attempt(
            diagnostic_id=diagnostic.id,
            student_id=diagnostic.student_id,
            answers=graded_answers,
            baseline_mastery_updates=[item.model_dump() for item in baseline_updates],
            recommended_start_topic_id=recommended_start_topic_id,
            score=score,
        )
        repo.mark_submitted(diagnostic)
        from backend.services.lesson_cockpit_service import LessonCockpitService
        from backend.services.lesson_experience_service import LessonExperienceService
        from backend.services.course_experience_service import CourseExperienceService

        LessonExperienceService.invalidate_topic_snapshot_cache(
            student_id=payload.student_id,
            subject=diagnostic.subject,
            sss_level=diagnostic.sss_level,
            term=int(diagnostic.term),
        )
        LessonCockpitService.invalidate_scope_cache(
            student_id=payload.student_id,
            subject=diagnostic.subject,
            sss_level=diagnostic.sss_level,
            term=int(diagnostic.term),
        )
        CourseExperienceService.invalidate_scope_cache(
            student_id=payload.student_id,
            subject=diagnostic.subject,
            sss_level=diagnostic.sss_level,
            term=int(diagnostic.term),
        )
        db.commit()

        return DiagnosticSubmitOut(
            baseline_mastery_updates=baseline_updates,
            recommended_start_topic_id=recommended_start_topic_id,
            recommended_start_topic_title=recommended_start_topic_title,
            scope_warning=scope_warning,
        )


diagnostic_service = DiagnosticService()

