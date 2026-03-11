import importlib
import importlib.util
import inspect
from types import SimpleNamespace
from uuid import uuid4

import pytest


if importlib.util.find_spec("backend.services.learning_path_service") is None:
    pytest.skip(
        "Section 3 Lane B pending: backend.services.learning_path_service is not created yet.",
        allow_module_level=True,
    )


learning_path_service_module = importlib.import_module("backend.services.learning_path_service")
PathNextIn = importlib.import_module("backend.schemas.learning_path_schema").PathNextIn


def test_learning_path_service_contract_is_exposed():
    assert hasattr(learning_path_service_module, "learning_path_service")

    service = learning_path_service_module.learning_path_service
    assert callable(getattr(service, "calculate_next_step", None))
    assert callable(getattr(service, "get_learning_map_visual", None))


def test_learning_path_service_signature_includes_db_and_payload():
    service = learning_path_service_module.learning_path_service
    params = inspect.signature(service.calculate_next_step).parameters

    assert "db" in params and "payload" in params


def test_learning_map_visual_signature_includes_required_args():
    service = learning_path_service_module.learning_path_service
    params = inspect.signature(service.get_learning_map_visual).parameters

    for expected in ("db", "student_id", "subject", "sss_level", "term", "view"):
        assert expected in params


def test_calculate_next_step_raises_when_scope_has_no_mapped_concepts(monkeypatch):
    service = learning_path_service_module.learning_path_service
    student_id = uuid4()
    topics = [SimpleNamespace(id=uuid4(), title="Our Values")]
    payload = PathNextIn(student_id=student_id, subject="civic", sss_level="SSS1", term=1)

    monkeypatch.setattr(
        service,
        "_scope_graph_rows",
        lambda **_: (topics, [], {}),
    )

    with pytest.raises(learning_path_service_module.LearningPathValidationError):
        service.calculate_next_step(db=object(), payload=payload)


def test_calculate_next_step_includes_unmapped_topic_warning(monkeypatch):
    service = learning_path_service_module.learning_path_service
    student_id = uuid4()
    mapped_topic = SimpleNamespace(id=uuid4(), title="Our Values")
    unmapped_topic = SimpleNamespace(id=uuid4(), title="Citizenship")
    payload = PathNextIn(student_id=student_id, subject="civic", sss_level="SSS1", term=1)
    concept_id = "civic:sss1:t1:our-values"

    monkeypatch.setattr(
        service,
        "_scope_graph_rows",
        lambda **_: (
            [mapped_topic, unmapped_topic],
            [
                {
                    "topic_id": str(mapped_topic.id),
                    "topic_title": str(mapped_topic.title),
                    "concept_id": concept_id,
                    "prereq_concept_ids": [],
                }
            ],
            {concept_id: 0.2},
        ),
    )

    result = service.calculate_next_step(db=object(), payload=payload)

    assert result.recommended_topic_id == str(mapped_topic.id)
    assert result.recommended_concept_id == concept_id
    assert result.scope_warning is not None
    assert "Citizenship" in result.unmapped_topic_titles
