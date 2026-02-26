from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
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


MASTERY_PASS_THRESHOLD = 0.7


class DiagnosticValidationError(ValueError):
    pass


class DiagnosticNotFoundError(ValueError):
    pass


class DiagnosticAlreadySubmittedError(ValueError):
    pass


class DiagnosticService:
    @staticmethod
    def _topic_concept_id(topic_id) -> str:
        return str(topic_id)

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

        titles = [topic.title for topic in topics]
        questions: list[dict] = []
        for topic in topics:
            question_id = str(uuid4())
            concept_id = self._topic_concept_id(topic.id)
            options = self._build_options(
                correct_title=topic.title,
                other_titles=titles,
            )
            questions.append(
                {
                    "question_id": question_id,
                    "concept_id": concept_id,
                    "topic_id": str(topic.id),
                    "prompt": f"Which option best matches the topic '{topic.title}'?",
                    "options": options,
                    "correct_answer": "A",
                }
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
        if topics:
            for topic in topics:
                concept_id = self._topic_concept_id(topic.id)
                if existing_mastery.get(concept_id, 0.0) < MASTERY_PASS_THRESHOLD:
                    recommended_start_topic_id = str(topic.id)
                    break
            if recommended_start_topic_id is None:
                weakest = min(topics, key=lambda t: existing_mastery.get(self._topic_concept_id(t.id), 1.0))
                recommended_start_topic_id = str(weakest.id)

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
        db.commit()

        return DiagnosticSubmitOut(
            baseline_mastery_updates=baseline_updates,
            recommended_start_topic_id=recommended_start_topic_id,
        )


diagnostic_service = DiagnosticService()

