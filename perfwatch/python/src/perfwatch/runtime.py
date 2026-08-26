from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from argparse import SUPPRESS, ArgumentParser, Namespace
from collections.abc import Sequence
from pathlib import Path

import httpx
import uvicorn

from perfwatch.config.settings import Settings

STARTUP_TIMEOUT_SECONDS = 5.0
SHUTDOWN_TIMEOUT_SECONDS = 5.0


def bundle_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[3]


def default_data_directory() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("LOCALAPPDATA is required for the packaged Windows runtime")
    return Path(local_app_data) / "PerfWatch"


def self_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable]
    return [sys.executable, "-m", "perfwatch.runtime"]


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Run the PerfWatch Windows application")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--database-path", type=Path)
    parser.add_argument("--dashboard-directory", type=Path)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--no-overlay", action="store_true")
    parser.add_argument("--overlay-child", action="store_true", help=SUPPRESS)
    parser.add_argument(
        "--snapshot-url",
        default="http://127.0.0.1:8000/snapshot",
        help=SUPPRESS,
    )
    parser.add_argument("--parent-pid", type=int, help=SUPPRESS)
    return parser


def _dashboard_directory(args: Namespace) -> Path:
    if args.dashboard_directory is not None:
        return args.dashboard_directory.resolve()
    if getattr(sys, "frozen", False):
        return bundle_root() / "dashboard"
    return bundle_root() / "ui" / "dashboard" / "dist"


def _base_url(host: str, port: int) -> str:
    connect_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    url_host = f"[{connect_host}]" if ":" in connect_host else connect_host
    return f"http://{url_host}:{port}"


def _wait_until_ready(base_url: str, server_thread: threading.Thread) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    last_error = "service did not respond"
    with httpx.Client(timeout=0.5) as client:
        while time.monotonic() < deadline:
            if not server_thread.is_alive():
                raise RuntimeError("service exited during startup")
            try:
                for path in ("/health", "/snapshot", "/"):
                    response = client.get(f"{base_url}{path}")
                    if response.status_code != 200:
                        raise RuntimeError(f"{path} returned HTTP {response.status_code}")
                return
            except (httpx.HTTPError, RuntimeError) as error:
                last_error = str(error)
                time.sleep(0.1)
    raise RuntimeError(f"service readiness timed out: {last_error}")


def _stop_overlay(process: subprocess.Popen[bytes]) -> bool:
    if process.poll() is not None:
        return True
    process.terminate()
    try:
        process.wait(timeout=SHUTDOWN_TIMEOUT_SECONDS)
        return True
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        return False


def _raise_keyboard_interrupt(_signum: int, _frame: object) -> None:
    raise KeyboardInterrupt


def _run_application(args: Namespace) -> int:
    data_directory = default_data_directory()
    data_directory.mkdir(parents=True, exist_ok=True)
    database_path = (args.database_path or data_directory / "perfwatch.sqlite3").resolve()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    dashboard_directory = _dashboard_directory(args)
    if not (dashboard_directory / "index.html").is_file():
        raise RuntimeError(f"dashboard build not found: {dashboard_directory / 'index.html'}")

    os.environ["PERFWATCH_DATABASE_PATH"] = str(database_path)
    os.environ["PERFWATCH_USE_MOCK_COLLECTOR"] = "true" if args.mock else "false"
    from perfwatch.api.app import create_app

    settings = Settings(database_path=database_path, use_mock_collector=args.mock)
    application = create_app(settings=settings, dashboard_directory=dashboard_directory)
    server = uvicorn.Server(uvicorn.Config(application, host=args.host, port=args.port))
    server_thread = threading.Thread(
        target=server.run,
        name="perfwatch-server",
        daemon=False,
    )
    overlay: subprocess.Popen[bytes] | None = None
    exit_code = 0
    server_thread.start()
    previous_sigbreak = None
    try:
        if sys.platform == "win32":
            previous_sigbreak = signal.signal(signal.SIGBREAK, _raise_keyboard_interrupt)
        base_url = _base_url(args.host, args.port)
        _wait_until_ready(base_url, server_thread)
        print(f"PerfWatch Dashboard: {base_url}/")
        if not args.no_overlay:
            overlay = subprocess.Popen(
                self_command()
                + [
                    "--overlay-child",
                    "--snapshot-url",
                    f"{base_url}/snapshot",
                    "--parent-pid",
                    str(os.getpid()),
                ]
            )

        while server_thread.is_alive():
            if overlay is not None and overlay.poll() is not None:
                print("PerfWatch overlay exited unexpectedly", file=sys.stderr)
                exit_code = 1
                break
            server_thread.join(timeout=0.25)
        if not server_thread.is_alive() and not server.should_exit:
            print("PerfWatch service exited unexpectedly", file=sys.stderr)
            exit_code = 1
    except KeyboardInterrupt:
        pass
    except Exception as error:
        print(f"PerfWatch startup failed: {error}", file=sys.stderr)
        exit_code = 1
    finally:
        if previous_sigbreak is not None:
            signal.signal(signal.SIGBREAK, previous_sigbreak)
        server.should_exit = True
        if overlay is not None and not _stop_overlay(overlay):
            print("PerfWatch overlay required forced termination", file=sys.stderr)
            exit_code = 1
        server_thread.join()
    return exit_code


def main(argv: Sequence[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    if args.overlay_child:
        from perfwatch.overlay import run_overlay

        run_overlay(args.snapshot_url, parent_pid=args.parent_pid)
        return 0
    try:
        return _run_application(args)
    except Exception as error:
        print(f"PerfWatch startup failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
