from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.schemas.quiz_schema import QuizGenerateRequest, QuizGenerateResponse, QuestionSchema
from backend.repositories.quiz_repo import QuizRepository
# Import AI core client (placeholder)
from backend.core.ai_core_client import generate_quiz_questions  # hypothetical client

class QuizGenerateService:
    def __init__(self, db: Session):
        self.repo = QuizRepository(db)

    async def generate_quiz(self, request: QuizGenerateRequest) -> QuizGenerateResponse:
        # 1. Validate prerequisites? (optional)
        # 2. Call AI core to generate questions
        try:
            # This function would call the ai-core quiz_engine
            questions_data = await generate_quiz_questions(
                subject=request.subject,
                sss_level=request.sss_level,
                term=request.term,
                topic_id=request.topic_id,
                purpose=request.purpose,
                difficulty=request.difficulty,
                num_questions=request.num_questions
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail=f"AI generation failed: {str(e)}")

        # 3. Store quiz and questions in DB
        quiz = self.repo.create_quiz(
            student_id=request.student_id,
            subject=request.subject,
            sss_level=request.sss_level,
            term=request.term,
            topic_id=request.topic_id,
            purpose=request.purpose,
            difficulty=request.difficulty,
            num_questions=request.num_questions,
        )
        for idx, q in enumerate(questions_data):
            q["order"] = idx
            self.repo.add_question_to_quiz(quiz.id, q)

        # 4. Build response
        questions = [
            QuestionSchema(
                id=q["id"],
                text=q["text"],
                options=q.get("options"),
                correct_answer=q.get("correct_answer"),  # may omit for security
                concept_id=q["concept_id"],
                difficulty=q["difficulty"]
            ) for q in questions_data
        ]
        return QuizGenerateResponse(quiz_id=quiz.id, questions=questions)
