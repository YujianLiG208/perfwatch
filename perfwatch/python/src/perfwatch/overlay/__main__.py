from __future__ import annotations

from argparse import ArgumentParser
from collections.abc import Sequence

from perfwatch.overlay.win32 import run_overlay


def main(argv: Sequence[str] | None = None) -> None:
    parser = ArgumentParser(description="Run the PerfWatch Windows overlay")
    parser.add_argument(
        "--snapshot-url",
        default="http://127.0.0.1:8000/snapshot",
    )
    parser.add_argument("--interval-seconds", type=float, default=1.0)
    parser.add_argument("--parent-pid", type=int)
    args = parser.parse_args(argv)
    if args.interval_seconds <= 0:
        parser.error("--interval-seconds must be positive")
    run_overlay(args.snapshot_url, args.interval_seconds, args.parent_pid)


if __name__ == "__main__":
    main()
