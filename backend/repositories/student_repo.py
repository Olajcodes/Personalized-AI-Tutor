"""Student repository (stub).

Logic:
- Real implementation should query student profile table.
- For MVP scaffolding, return a mock student scope context.
"""

from sqlalchemy.orm import Session

def get_student_scope(db: Session, student_id: str) -> dict:
    # TODO: Replace with real DB query
    return {"student_id": student_id, "sss_level": "SSS1", "term": 1, "subjects": ["math","english","civic"]}
