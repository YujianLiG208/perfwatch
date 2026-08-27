from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI

from perfwatch import server


def test_parser_uses_local_defaults() -> None:
    args = server.create_parser().parse_args([])

    assert args.host == "127.0.0.1"
    assert args.port == 8000
    assert args.dashboard_directory == (
        Path(__file__).resolve().parents[2] / "ui" / "dashboard" / "dist"
    )


def test_default_dashboard_directory_uses_frozen_bundle(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(server.sys, "frozen", True, raising=False)
    monkeypatch.setattr(server.sys, "_MEIPASS", str(tmp_path), raising=False)

    assert server.default_dashboard_directory() == tmp_path / "dashboard"


def test_parser_accepts_explicit_server_options(tmp_path) -> None:
    args = server.create_parser().parse_args(
        [
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
            "--dashboard-directory",
            str(tmp_path),
        ]
    )

    assert args.host == "0.0.0.0"
    assert args.port == 9000
    assert args.dashboard_directory == tmp_path


def test_main_rejects_dashboard_without_index_html(tmp_path, monkeypatch) -> None:
    def fail_if_started(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("uvicorn.run must not be called")

    monkeypatch.setattr(server.uvicorn, "run", fail_if_started)

    with pytest.raises(SystemExit) as error:
        server.main(["--dashboard-directory", str(tmp_path)])

    assert error.value.code == 2


def test_main_runs_combined_application(tmp_path, monkeypatch) -> None:
    dashboard_directory = tmp_path / "dashboard"
    dashboard_directory.mkdir()
    (dashboard_directory / "index.html").write_text(
        "<h1>PerfWatch dashboard</h1>",
        encoding="utf-8",
    )
    calls: list[tuple[FastAPI, str, int]] = []

    def record_run(application: FastAPI, *, host: str, port: int) -> None:
        calls.append((application, host, port))

    monkeypatch.setattr(server.uvicorn, "run", record_run)

    server.main(
        [
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
            "--dashboard-directory",
            str(dashboard_directory),
        ]
    )

    assert len(calls) == 1
    application, host, port = calls[0]
    assert host == "0.0.0.0"
    assert port == 9000
    assert any(
        getattr(route, "name", None) == "dashboard" for route in application.routes
    )
