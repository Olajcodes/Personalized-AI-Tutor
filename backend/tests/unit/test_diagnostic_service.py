import importlib
import importlib.util
import inspect

import pytest


if importlib.util.find_spec("backend.services.diagnostic_service") is None:
    pytest.skip(
        "Section 3 Lane B pending: backend.services.diagnostic_service is not created yet.",
        allow_module_level=True,
    )


diagnostic_service_module = importlib.import_module("backend.services.diagnostic_service")


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
