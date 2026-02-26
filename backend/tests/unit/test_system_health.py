from backend.endpoints import system


def test_health_ok_when_postgres_ok(monkeypatch):
    monkeypatch.setattr(system, "_check_postgres", lambda: {"status": "ok"})

    out = system.health()

    assert out["status"] == "ok"
    assert out["checks"]["postgres"]["status"] == "ok"


def test_health_degraded_when_postgres_fails(monkeypatch):
    monkeypatch.setattr(system, "_check_postgres", lambda: {"status": "error", "detail": "boom"})

    out = system.health()

    assert out["status"] == "degraded"
    assert out["checks"]["postgres"]["status"] == "error"
