import sys
from types import ModuleType

import pytest

from perfwatch.collectors.mock import MockCollector, get_mock_snapshot
from perfwatch.collectors.native import NativeCollector


def test_mock_snapshot_preserves_baseline_and_evolves() -> None:
    baseline = get_mock_snapshot(0)
    next_snapshot = get_mock_snapshot(1)

    assert baseline["timestamp_ms"] == 1_710_000_000_000
    assert baseline["cpu"]["usage_percent"] == 42.5
    assert baseline["top_processes"][0]["name"] == "mock_process"
    assert next_snapshot["timestamp_ms"] == 1_710_000_001_000
    assert next_snapshot["cpu"]["usage_percent"] > baseline["cpu"]["usage_percent"]


def test_mock_collectors_advance_independently() -> None:
    first_collector = MockCollector()
    second_collector = MockCollector()

    assert first_collector.collect() == second_collector.collect()
    assert first_collector.collect()["timestamp_ms"] == 1_710_000_001_000
    assert second_collector.collect()["timestamp_ms"] == 1_710_000_001_000


def test_mock_snapshot_rejects_negative_index() -> None:
    with pytest.raises(ValueError, match="sample_index must be non-negative"):
        get_mock_snapshot(-1)


def _fake_native_module(calls: list[int]) -> ModuleType:
    module = ModuleType("perfwatch_native")

    class FakeWindowsCollector:
        def __init__(self) -> None:
            self.sample_index = 0

        def collect(self) -> dict[str, object]:
            calls.append(self.sample_index)
            snapshot = get_mock_snapshot(self.sample_index)
            self.sample_index += 1
            return snapshot

    setattr(module, "WindowsCollector", FakeWindowsCollector)
    return module


def test_native_wrapper_uses_stateful_windows_collector(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []
    monkeypatch.setitem(sys.modules, "perfwatch_native", _fake_native_module(calls))

    first_collector = NativeCollector()
    second_collector = NativeCollector()

    assert first_collector.collect()["timestamp_ms"] == 1_710_000_000_000
    assert first_collector.collect()["timestamp_ms"] == 1_710_000_001_000
    assert second_collector.collect()["timestamp_ms"] == 1_710_000_000_000
    assert calls == [0, 1, 0]


def test_native_collector_never_falls_back_to_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "perfwatch_native", None)
    collector = NativeCollector()

    with pytest.raises(RuntimeError, match="live Windows collector unavailable"):
        collector.collect()
