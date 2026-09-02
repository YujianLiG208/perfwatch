from __future__ import annotations

from typing import Any

class NativeCollector:
    def __init__(self) -> None:
        try:
            from perfwatch_native import WindowsCollector  # type: ignore[import-not-found]
        except (ImportError, AttributeError) as error:
            self._collector = None
            self._import_error = error
        else:
            self._collector = WindowsCollector()
            self._import_error = None

    def collect(self) -> dict[str, Any]:
        if self._collector is None:
            raise RuntimeError(
                "live Windows collector unavailable; explicitly enable mock mode for tests"
            ) from self._import_error
        return self._collector.collect()
