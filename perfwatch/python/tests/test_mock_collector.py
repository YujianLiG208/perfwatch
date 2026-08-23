import sys
from types import ModuleType

import pytest

from perfwatch.collectors.mock import MockCollector, get_mock_snapshot
from perfwatch.collectors.native import NativeCollector, get_snapshot


def test_mock_snapshot_index_zero_preserves_baseline() -> None:
    snapshot = get_mock_snapshot(0)

    assert snapshot["timestamp_ms"] == 1_710_000_000_000
    assert {"cpu", "memory", "battery", "gpu", "top_processes"} <= snapshot.keys()
    assert snapshot["cpu"]["usage_percent"] == 42.5
    assert snapshot["memory"]["used_bytes"] == 17_179_869_184
    assert snapshot["battery"]["percent"] == 78.0
    assert snapshot["top_processes"][0]["name"] == "mock_process"
    assert snapshot["top_processes"][0]["estimated_power_score"] == 0.42


def test_mock_snapshot_follows_formulas_at_explicit_index() -> None:
    snapshot = get_mock_snapshot(3)

    assert snapshot["timestamp_ms"] == 1_710_000_003_000
    assert snapshot["cpu"]["usage_percent"] == 47.0
    assert snapshot["memory"]["used_bytes"] == 17_381_195_776
    assert snapshot["battery"]["percent"] == 77.25
    assert snapshot["battery"]["power_watts"] == pytest.approx(19.4)
    assert snapshot["top_processes"][0]["cpu_percent"] == pytest.approx(14.6)
    assert snapshot["top_processes"][0]["rss_bytes"] == 281_018_368
    assert snapshot["top_processes"][0]["estimated_power_score"] == pytest.approx(0.45)


def test_mock_snapshot_repeats_same_explicit_index() -> None:
    assert get_mock_snapshot(3) == get_mock_snapshot(3)


def test_mock_collectors_advance_independently() -> None:
    first_collector = MockCollector()
    second_collector = MockCollector()

    assert first_collector.collect() == second_collector.collect()
    assert first_collector.collect()["timestamp_ms"] == 1_710_000_001_000
    assert second_collector.collect()["timestamp_ms"] == 1_710_000_001_000


@pytest.mark.parametrize(
    ("sample_index", "charging", "battery_percent"),
    [
        (40, False, 68.0),
        (41, True, 68.25),
        (80, False, 78.0),
    ],
)
def test_mock_snapshot_keeps_battery_cycle_bounded(
    sample_index: int,
    charging: bool,
    battery_percent: float,
) -> None:
    snapshot = get_mock_snapshot(sample_index)

    assert snapshot["battery"]["charging"] is charging
    assert snapshot["battery"]["percent"] == battery_percent


def test_mock_snapshot_rejects_negative_index() -> None:
    with pytest.raises(ValueError, match="sample_index must be non-negative"):
        get_mock_snapshot(-1)


def _fake_native_module(calls: list[int]) -> ModuleType:
    module = ModuleType("perfwatch_native")

    def fake_get_mock_snapshot(sample_index: int = 0) -> dict[str, object]:
        calls.append(sample_index)
        return get_mock_snapshot(sample_index)

    setattr(module, "get_mock_snapshot", fake_get_mock_snapshot)
    return module


def test_native_get_snapshot_forwards_optional_index(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []
    monkeypatch.setitem(sys.modules, "perfwatch_native", _fake_native_module(calls))

    assert get_snapshot()["timestamp_ms"] == 1_710_000_000_000
    assert get_snapshot(3)["timestamp_ms"] == 1_710_000_003_000
    assert calls == [0, 3]


def test_native_collectors_advance_independently(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []
    monkeypatch.setitem(sys.modules, "perfwatch_native", _fake_native_module(calls))
    first_collector = NativeCollector()
    second_collector = NativeCollector()

    assert first_collector.collect()["timestamp_ms"] == 1_710_000_000_000
    assert first_collector.collect()["timestamp_ms"] == 1_710_000_001_000
    assert second_collector.collect()["timestamp_ms"] == 1_710_000_000_000
    assert calls == [0, 1, 0]


def test_native_collector_fallback_advances(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "perfwatch_native", None)
    collector = NativeCollector()

    assert collector.collect()["timestamp_ms"] == 1_710_000_000_000
    assert collector.collect()["timestamp_ms"] == 1_710_000_001_000
