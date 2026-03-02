import importlib
import importlib.util
import inspect

import pytest


if importlib.util.find_spec("backend.services.learning_path_service") is None:
    pytest.skip(
        "Section 3 Lane B pending: backend.services.learning_path_service is not created yet.",
        allow_module_level=True,
    )


learning_path_service_module = importlib.import_module("backend.services.learning_path_service")


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
