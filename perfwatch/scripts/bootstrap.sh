#!/usr/bin/env bash
set -eu

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_DIR="$ROOT_DIR/python"

python3 -m venv "$PYTHON_DIR/.venv"
"$PYTHON_DIR/.venv/bin/python" -m pip install --upgrade pip
"$PYTHON_DIR/.venv/bin/python" -m pip install -e "$PYTHON_DIR[dev]"
