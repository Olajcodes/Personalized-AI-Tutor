from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException, status
from datetime import datetime

from backend.schemas.quiz_schema import QuizSubmitRequest, QuizSubmitResponse, ConceptBreakdownItem
from backend.repositories.quiz_repo import QuizRepository
from backend.services.graph_mastery_update_service import GraphMasteryUpdateService
from backend.services.activity_service import ActivityService  # from Section 1
from backend.models.quiz import QuizQuestion

class QuizSubmitService:
    def __init__(self, db: Session):
        self.repo = QuizRepository(db)
        self.graph_service = GraphMasteryUpdateService(db)
        self.activity_service = ActivityService(db)

    async def submit_quiz(self, quiz_id: UUID, request: QuizSubmitRequest) -> QuizSubmitResponse:
        # 1. Fetch quiz and questions
        quiz = self.repo.get_quiz_with_questions(quiz_id)
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
        questions = self.repo.get_questions_for_quiz(quiz_id)
        question_map = {q.id: q for q in questions}

        # 2. Score answers
        total_questions = len(questions)
        correct_count = 0
        concept_results = []  # list of (concept_id, correct)
        for ans in request.answers:
            qid = ans["question_id"]
            if qid not in question_map:
                continue  # skip invalid question ids
            q = question_map[qid]
            is_correct = (ans["answer"].strip().lower() == q.correct_answer.strip().lower())
            if is_correct:
                correct_count += 1
            concept_results.append((q.concept_id, is_correct))

        score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        xp = int(score)  # simple mapping: 1 XP per percent

        # 3. Save attempt and answers
        attempt = self.repo.create_attempt(quiz_id, request.student_id, request.time_taken_seconds)
        # Prepare answers with is_correct flag
        answers_with_score = []
        for ans in request.answers:
            qid = ans["question_id"]
            if qid in question_map:
                is_correct = (ans["answer"].strip().lower() == question_map[qid].correct_answer.strip().lower())
                answers_with_score.append({
                    "question_id": qid,
                    "answer": ans["answer"],
                    "is_correct": is_correct
                })
        self.repo.save_answers(attempt.id, answers_with_score)
        self.repo.update_attempt_score(attempt.id, score, xp)

        # 4. Log activity
        await self.activity_service.log_activity(
            student_id=request.student_id,
            subject=quiz.subject,  # need to store subject on quiz? currently not in model. We'll need to add subject to quiz model.
            term=quiz.term,
            event_type="quiz_submitted",
            ref_id=quiz_id,
            duration_seconds=request.time_taken_seconds
        )

        # 5. Trigger graph mastery update
        concept_breakdown = [
            ConceptBreakdownItem(concept_id=cid, correct=correct, mastery_delta=0.15 if correct else -0.05)
            for cid, correct in concept_results
        ]
        await self.graph_service.send_update(
            student_id=request.student_id,
            quiz_id=quiz_id,
            attempt_id=attempt.id,
            subject=quiz.subject,  # need subject field
            sss_level=quiz.sss_level,  # need sss_level field
            term=quiz.term,  # need term field
            source=quiz.purpose,
            concept_breakdown=concept_breakdown
        )

        return QuizSubmitResponse(attempt_id=attempt.id, score=score, xp_awarded=xp)