#!/usr/bin/env bash
set -eu

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

python -m pytest python/tests

if command -v cmake >/dev/null 2>&1; then
    cmake -S cpp -B build
    cmake --build build --config Debug
    ctest --test-dir build --output-on-failure -C Debug
fi
