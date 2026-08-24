from fastapi.testclient import TestClient
import pytest

from perfwatch.api.app import create_app
from perfwatch.collectors.mock import MockCollector
from perfwatch.config.settings import Settings


def test_health_returns_ok(tmp_path) -> None:
    app = create_app(
        settings=Settings(
            database_path=tmp_path / "health.sqlite3",
            snapshot_interval_seconds=60.0,
            use_mock_collector=True,
        ),
        collector=MockCollector(),
    )

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_snapshot_returns_expected_keys(tmp_path) -> None:
    app = create_app(
        settings=Settings(
            database_path=tmp_path / "snapshot.sqlite3",
            snapshot_interval_seconds=60.0,
            use_mock_collector=True,
        ),
        collector=MockCollector(),
    )

    with TestClient(app) as client:
        response = client.get("/snapshot")

    assert response.status_code == 200
    data = response.json()
    assert {"timestamp_ms", "cpu", "memory", "battery", "gpu", "top_processes"} <= data.keys()
    assert data["battery"]["estimated_remaining_seconds"] == pytest.approx(
        8_756.756756756757
    )
    assert data["top_processes"][0]["estimated_power_score"] == pytest.approx(0.1)


def test_recent_metrics_returns_persisted_samples(tmp_path) -> None:
    app = create_app(
        settings=Settings(
            database_path=tmp_path / "metrics.sqlite3",
            snapshot_interval_seconds=60.0,
            use_mock_collector=True,
        ),
        collector=MockCollector(),
    )

    with TestClient(app) as client:
        response = client.get("/metrics/recent", params={"limit": 1})

    assert response.status_code == 200
    metrics = response.json()
    assert len(metrics) == 1
    assert metrics[0]["timestamp_ms"] == 1710000000000
    assert metrics[0]["cpu"]["usage_percent"] == 42.5
    assert metrics[0]["battery"]["estimated_remaining_seconds"] == pytest.approx(
        8_756.756756756757
    )


def test_top_processes_returns_latest_sample(tmp_path) -> None:
    app = create_app(
        settings=Settings(
            database_path=tmp_path / "processes.sqlite3",
            snapshot_interval_seconds=60.0,
            use_mock_collector=True,
        ),
        collector=MockCollector(),
    )

    with TestClient(app) as client:
        response = client.get("/processes/top", params={"limit": 1})

    assert response.status_code == 200
    processes = response.json()
    assert len(processes) == 1
    assert processes[0]["name"] == "mock_process"
    assert processes[0]["estimated_power_score"] == pytest.approx(0.1)


def test_snapshot_websocket_streams_latest_snapshot(tmp_path) -> None:
    app = create_app(
        settings=Settings(
            database_path=tmp_path / "websocket.sqlite3",
            snapshot_interval_seconds=60.0,
            use_mock_collector=True,
        ),
        collector=MockCollector(),
    )

    with TestClient(app) as client:
        with client.websocket_connect("/ws/snapshot") as websocket:
            snapshot = websocket.receive_json()

    assert snapshot["timestamp_ms"] == 1710000000000
    assert snapshot["battery"]["estimated_remaining_seconds"] == pytest.approx(
        8_756.756756756757
    )
    assert snapshot["top_processes"][0]["name"] == "mock_process"
    assert snapshot["top_processes"][0]["estimated_power_score"] == pytest.approx(0.1)
