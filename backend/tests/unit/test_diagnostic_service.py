import importlib
import importlib.util
import inspect
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import MagicMock

import pytest


if importlib.util.find_spec("backend.services.diagnostic_service") is None:
    pytest.skip(
        "Section 3 Lane B pending: backend.services.diagnostic_service is not created yet.",
        allow_module_level=True,
    )


diagnostic_service_module = importlib.import_module("backend.services.diagnostic_service")
DiagnosticStartIn = importlib.import_module("backend.schemas.diagnostic_schema").DiagnosticStartIn


def test_diagnostic_service_contract_is_exposed():
    assert hasattr(diagnostic_service_module, "diagnostic_service")

    service = diagnostic_service_module.diagnostic_service
    assert callable(getattr(service, "create_diagnostic_session", None))
    assert callable(getattr(service, "process_diagnostic_submission", None))


def test_diagnostic_service_method_signatures_include_db_and_payload():
    service = diagnostic_service_module.diagnostic_service

    start_params = inspect.signature(service.create_diagnostic_session).parameters
    submit_params = inspect.signature(service.process_diagnostic_submission).parameters

    assert "db" in start_params and "payload" in start_params
    assert "db" in submit_params and "payload" in submit_params


def test_create_diagnostic_session_requires_mapped_curriculum_concepts(monkeypatch):
    repo = MagicMock()
    repo.validate_student_scope.return_value = True
    repo.get_scope_topics.return_value = [SimpleNamespace(id=uuid4(), title="Our Values")]
    repo.get_scope_topic_concept_rows.return_value = []

    monkeypatch.setattr(diagnostic_service_module, "DiagnosticRepository", lambda db: repo)

    payload = DiagnosticStartIn(
        student_id=uuid4(),
        subject="civic",
        sss_level="SSS1",
        term=1,
    )

    with pytest.raises(diagnostic_service_module.DiagnosticValidationError):
        diagnostic_service_module.diagnostic_service.create_diagnostic_session(db=object(), payload=payload)


def test_create_diagnostic_session_uses_real_concept_labels(monkeypatch):
    topic_id = uuid4()
    repo = MagicMock()
    repo.validate_student_scope.return_value = True
    repo.get_scope_topics.return_value = [SimpleNamespace(id=topic_id, title="Our Values")]
    repo.get_scope_topic_concept_rows.return_value = [
        {
            "topic_id": str(topic_id),
            "topic_title": "Our Values",
            "concept_id": "civic:sss1:t1:individualistic-values",
            "prereq_concept_ids": [],
        }
    ]
    repo.create_diagnostic.side_effect = lambda **kwargs: SimpleNamespace(id=uuid4(), **kwargs)

    monkeypatch.setattr(diagnostic_service_module, "DiagnosticRepository", lambda db: repo)

    payload = DiagnosticStartIn(
        student_id=uuid4(),
        subject="civic",
        sss_level="SSS1",
        term=1,
    )

    result = diagnostic_service_module.diagnostic_service.create_diagnostic_session(db=MagicMock(), payload=payload)

    assert result.questions[0].concept_id == "civic:sss1:t1:individualistic-values"
    assert result.questions[0].concept_label == "Individualistic Values"
    assert result.questions[0].topic_title == "Our Values"
