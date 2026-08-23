from __future__ import annotations

from typing import Any

from perfwatch.collectors.mock import get_mock_snapshot as get_python_mock_snapshot


def get_snapshot(sample_index: int = 0) -> dict[str, Any]:
    try:
        from perfwatch_native import (  # type: ignore[import-not-found]
            get_mock_snapshot as get_native_mock_snapshot,
        )
    except ImportError:
        return get_python_mock_snapshot(sample_index)

    return get_native_mock_snapshot(sample_index)


class NativeCollector:
    def __init__(self) -> None:
        self._sample_index = 0

    def collect(self) -> dict[str, Any]:
        snapshot = get_snapshot(self._sample_index)
        self._sample_index += 1
        return snapshot
