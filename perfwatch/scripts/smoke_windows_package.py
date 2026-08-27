from __future__ import annotations

import argparse
import json
import signal
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

MOCK_TIMESTAMP_MS = 1_710_000_000_000


def _unused_port(host: str) -> int:
    with socket.socket() as listener:
        listener.bind((host, 0))
        return int(listener.getsockname()[1])


def _read(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=0.5) as response:
        if response.status != 200:
            raise RuntimeError(f"{url} returned HTTP {response.status}")
        return response.read()


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the packaged PerfWatch application")
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()
    executable = args.executable.resolve()
    if not executable.is_file():
        parser.error(f"executable not found: {executable}")

    port = _unused_port(args.host)
    base_url = f"http://{args.host}:{port}"
    process = subprocess.Popen(
        [
            str(executable),
            "--mock",
            "--no-overlay",
            "--host",
            args.host,
            "--port",
            str(port),
        ],
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    try:
        deadline = time.monotonic() + args.timeout
        last_error = "application did not respond"
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"application exited early with code {process.returncode}")
            try:
                _read(f"{base_url}/health")
                snapshot = json.loads(_read(f"{base_url}/snapshot"))
                _read(f"{base_url}/")
                if snapshot.get("timestamp_ms") != MOCK_TIMESTAMP_MS:
                    raise RuntimeError("snapshot did not contain the explicit mock baseline")
                break
            except (OSError, RuntimeError, ValueError) as error:
                last_error = str(error)
                time.sleep(0.1)
        else:
            raise RuntimeError(f"package smoke timed out: {last_error}")

        process.send_signal(signal.CTRL_BREAK_EVENT)
        try:
            return_code = process.wait(timeout=10.0)
        except subprocess.TimeoutExpired as error:
            process.kill()
            process.wait()
            raise RuntimeError("packaged application did not stop") from error
        if return_code != 0:
            raise RuntimeError(f"packaged application exited with code {return_code}")
        print("Package smoke passed: /health, /snapshot, /, clean shutdown")
        return 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
