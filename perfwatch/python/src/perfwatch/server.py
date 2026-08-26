from __future__ import annotations

from argparse import ArgumentParser
from collections.abc import Sequence
from pathlib import Path
import sys

import uvicorn

from perfwatch.api.app import create_app
from perfwatch.runtime import bundle_root


def default_dashboard_directory() -> Path:
    if getattr(sys, "frozen", False):
        return bundle_root() / "dashboard"
    return bundle_root() / "ui" / "dashboard" / "dist"


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Run the PerfWatch local application")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--dashboard-directory",
        type=Path,
        default=default_dashboard_directory(),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = create_parser()
    args = parser.parse_args(argv)
    dashboard_directory = args.dashboard_directory.resolve()
    if not (dashboard_directory / "index.html").is_file():
        parser.error(
            f"dashboard build not found: {dashboard_directory / 'index.html'}"
        )
    app = create_app(dashboard_directory=dashboard_directory)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
