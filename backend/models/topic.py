"""Topic ORM model.

Logic:
- One topic is tied to (subject, SSS level, term).
- is_approved enforces curriculum governance.
"""

from sqlalchemy import Column, String, Integer, Boolean, Text
from backend.core.database import Base

class Topic(Base):
    __tablename__ = "topics"

    id = Column(String, primary_key=True)  # UUID as string (MVP)
    subject = Column(String, nullable=False, index=True)     # math|english|civic
    sss_level = Column(String, nullable=False, index=True)   # SSS1|SSS2|SSS3
    term = Column(Integer, nullable=False, index=True)       # 1|2|3
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    curriculum_version_id = Column(String, nullable=True, index=True)
    is_approved = Column(Boolean, default=False, index=True)
