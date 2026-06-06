"""Collector entry points."""

from typing import Any, Protocol

from perfwatch.collectors.mock import MockCollector
from perfwatch.collectors.native import NativeCollector, get_snapshot


class Collector(Protocol):
    def collect(self) -> dict[str, Any]: ...


def create_collector(*, use_mock: bool) -> Collector:
    if use_mock:
        return MockCollector()
    return NativeCollector()


__all__ = ["Collector", "create_collector", "get_snapshot"]
