from fastapi.testclient import TestClient

from perfwatch.api.app import app


def test_health_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_snapshot_returns_expected_keys() -> None:
    client = TestClient(app)

    response = client.get("/snapshot")

    assert response.status_code == 200
    data = response.json()
    assert {"timestamp_ms", "cpu", "memory", "battery", "gpu", "top_processes"} <= data.keys()
