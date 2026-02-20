"""Hard constraints: JSS1–JSS3 only and Term 1–3 only."""

from __future__ import annotations
from core_engine.config.constants import JSSLevel, Term


class CurriculumPolicyError(ValueError):
    pass


def assert_jss_level_allowed(jss_level: str) -> None:
    try:
        JSSLevel(jss_level)
    except Exception as e:
        raise CurriculumPolicyError(f"Unsupported JSS level: {jss_level}. Allowed: JSS1–JSS3.") from e


def assert_term_allowed(term: int) -> None:
    try:
        Term(term)
    except Exception as e:
        raise CurriculumPolicyError(f"Unsupported term: {term}. Allowed: 1–3.") from e
