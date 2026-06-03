from perfwatch.collectors.mock import get_mock_snapshot


def test_mock_collector_returns_expected_keys() -> None:
    snapshot = get_mock_snapshot()

    assert snapshot["timestamp_ms"] == 1710000000000
    assert {"cpu", "memory", "battery", "gpu", "top_processes"} <= snapshot.keys()
    assert snapshot["cpu"]["usage_percent"] == 42.5
    assert snapshot["top_processes"][0]["name"] == "mock_process"
