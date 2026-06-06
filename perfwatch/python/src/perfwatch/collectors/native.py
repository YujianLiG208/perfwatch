from __future__ import annotations

from typing import Any

from perfwatch.collectors.mock import get_mock_snapshot as get_python_mock_snapshot


def get_snapshot() -> dict[str, Any]:
    try:
        from perfwatch_native import (  # type: ignore[import-not-found]
            get_mock_snapshot as get_native_mock_snapshot,
        )
    except ImportError:
        return get_python_mock_snapshot()

    return get_native_mock_snapshot()


class NativeCollector:
    def collect(self) -> dict[str, Any]:
        return get_snapshot()
