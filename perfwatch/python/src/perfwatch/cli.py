from __future__ import annotations

import json

from perfwatch.collectors.native import get_snapshot


def main() -> None:
    print(json.dumps(get_snapshot(), indent=2, sort_keys=True))
