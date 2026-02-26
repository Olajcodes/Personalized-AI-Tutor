from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import List, Optional

from backend.models.quiz import Quiz
from backend.models.quiz_question import QuizQuestion
from backend.models.quiz_attempt import QuizAttempt
from backend.models.quiz_answer import QuizAnswer

class QuizRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Quiz Generation ---
    def create_quiz(
        self,
        *,
        student_id: UUID,
        subject: str,
        sss_level: str,
        term: int,
        topic_id: UUID,
        purpose: str,
        difficulty: str,
        num_questions: int,
    ) -> Quiz:
        quiz = Quiz(
            id=uuid4(),
            student_id=student_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
            topic_id=topic_id,
            purpose=purpose,
            difficulty=difficulty,
            num_questions=num_questions,
        )
        self.db.add(quiz)
        self.db.flush()
        return quiz

    def add_question_to_quiz(self, quiz_id: UUID, question_data: dict) -> QuizQuestion:
        """question_data should contain fields: text, options, correct_answer."""
        question = QuizQuestion(
            id=uuid4(),
            quiz_id=quiz_id,
            question_number=question_data.get("order", 0) + 1,
            question_text=question_data["text"],
            options=question_data.get("options"),
            correct_answer=question_data["correct_answer"],
        )
        self.db.add(question)
        self.db.flush()
        return question

    def get_quiz_with_questions(self, quiz_id: UUID) -> Optional[Quiz]:
        return self.db.query(Quiz).filter(Quiz.id == quiz_id).first()

    # --- Quiz Submission ---
    def create_attempt(self, quiz_id: UUID, student_id: UUID, time_taken: int) -> QuizAttempt:
        attempt = QuizAttempt(
            id=uuid4(),
            quiz_id=quiz_id,
            student_id=student_id,
            time_taken_seconds=time_taken,
        )
        self.db.add(attempt)
        self.db.flush()
        return attempt

    def save_answers(self, attempt_id: UUID, answers: List[dict]):
        for ans in answers:
            answer = QuizAnswer(
                id=uuid4(),
                attempt_id=attempt_id,
                question_id=ans["question_id"],
                selected_answer=ans["answer"],
                is_correct=ans.get("is_correct")  # will be set after scoring
            )
            self.db.add(answer)
        self.db.flush()

    def update_attempt_score(self, attempt_id: UUID, score: float, xp: int):
        _ = xp
        self.db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).update({
            "score": score,
        })
        self.db.flush()

    def get_attempt(self, attempt_id: UUID) -> Optional[QuizAttempt]:
        return self.db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()

    def get_attempt_with_answers(self, attempt_id: UUID) -> Optional[QuizAttempt]:
        attempt = self.db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
        if not attempt:
            return None
        answers = self.db.query(QuizAnswer).filter(QuizAnswer.attempt_id == attempt_id).all()
        setattr(attempt, "answers", answers)
        return attempt

    # --- Results ---
    def get_questions_for_quiz(self, quiz_id: UUID) -> List[QuizQuestion]:
        return (
            self.db.query(QuizQuestion)
            .filter(QuizQuestion.quiz_id == quiz_id)
            .order_by(QuizQuestion.question_number)
            .all()
        )
