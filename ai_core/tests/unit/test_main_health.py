from fastapi.testclient import TestClient

from ai_core.main import app


def test_health_reports_internal_service_key_configuration(monkeypatch):
    monkeypatch.setenv("INTERNAL_SERVICE_KEY", "secret-key")
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["checks"]["internal_service_key"] == "configured"
