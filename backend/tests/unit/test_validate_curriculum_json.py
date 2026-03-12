import json

import pytest

from backend.scripts.validate_curriculum_json import validate_curriculum_json_root
from backend.services.admin_curriculum_service import AdminCurriculumValidationError


def _write_json(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_validate_curriculum_json_root_flags_duplicate_topic_slugs(tmp_path):
    topic_payload = {
        "subject": "civic",
        "sss_level": "SSS1",
        "term": 1,
        "week": 2,
        "topic_title": "Our Values",
        "topic_slug": "our-values",
        "source_title": "First Term SS1 Civic Education",
        "learning_objectives": ["Define values"],
        "sections": [
            {"heading": "Meaning", "content": "Values are ideas and beliefs people hold as important in society."},
            {"heading": "Importance", "content": "Values guide decisions, behaviour, and priorities in everyday civic life."},
        ],
        "keywords": ["values"],
    }
    _write_json(tmp_path / "topic_a.json", topic_payload)
    _write_json(tmp_path / "topic_b.json", topic_payload)

    result = validate_curriculum_json_root(tmp_path)

    assert result["error_count"] == 1
    assert "duplicate topic_slug in same scope" in result["errors"][0]


def test_validate_curriculum_json_root_requires_files(tmp_path):
    with pytest.raises(AdminCurriculumValidationError):
        validate_curriculum_json_root(tmp_path)
