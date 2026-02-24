from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from backend.core.database import Base
from backend.core.config import settings

# Import models so Alembic can detect them
from backend.models.subject import Subject
from backend.models.student import StudentProfile, StudentSubject
from backend.models.topic import Topic
from backend.models.lesson import Lesson, LessonBlock
from backend.models.student import StudentProfile, StudentSubject, LearningPreference   

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_online():
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = settings.database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
