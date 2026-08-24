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


def test_dashboard_mount_preserves_http_and_websocket_routes(tmp_path) -> None:
    dashboard_directory = tmp_path / "dashboard"
    assets_directory = dashboard_directory / "assets"
    assets_directory.mkdir(parents=True)
    (dashboard_directory / "index.html").write_text(
        "<h1>PerfWatch dashboard</h1>",
        encoding="utf-8",
    )
    (assets_directory / "app.js").write_text(
        "window.perfwatch = true;",
        encoding="utf-8",
    )
    app = create_app(
        settings=Settings(
            database_path=tmp_path / "dashboard.sqlite3",
            snapshot_interval_seconds=60.0,
            use_mock_collector=True,
        ),
        collector=MockCollector(),
        dashboard_directory=dashboard_directory,
    )

    with TestClient(app) as client:
        root_response = client.get("/")
        asset_response = client.get("/assets/app.js")
        health_response = client.get("/health")
        snapshot_response = client.get("/snapshot")
        with client.websocket_connect("/ws/snapshot") as websocket:
            websocket_snapshot = websocket.receive_json()

    assert root_response.status_code == 200
    assert "PerfWatch dashboard" in root_response.text
    assert asset_response.status_code == 200
    assert asset_response.text == "window.perfwatch = true;"
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert snapshot_response.status_code == 200
    assert snapshot_response.json()["timestamp_ms"] == 1_710_000_000_000
    assert websocket_snapshot["timestamp_ms"] == 1_710_000_000_000
