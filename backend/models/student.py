import uuid
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from backend.core.database import Base

class StudentProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_profiles"

    # In MVP, user/auth may live elsewhere; we store a student_id for linking.
    # If later you create users table, make this a FK.
    student_id: Mapped[uuid.UUID] = mapped_column(unique=True, index=True, nullable=False)

    # "SSS1" | "SSS2" | "SSS3"
    sss_level: Mapped[str] = mapped_column(String(10), index=True, nullable=False)

    # 1 | 2 | 3
    active_term: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    subjects = relationship("StudentSubject", back_populates="student_profile", cascade="all, delete-orphan")


class StudentSubject(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_subjects"
    __table_args__ = (
        UniqueConstraint("student_profile_id", "subject_id", name="uq_student_subject"),
    )

    student_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)

    student_profile = relationship("StudentProfile", back_populates="subjects")
    subject = relationship("Subject")