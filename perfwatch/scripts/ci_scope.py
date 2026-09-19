from __future__ import annotations

import os
import subprocess


CHECKS = ("backend", "native", "frontend", "quality")


def checks_for_paths(paths: list[str]) -> set[str]:
    checks: set[str] = set()
    for path in paths:
        if path.endswith(".md"):
            continue
        if path.startswith((".github/workflows/", "perfwatch/scripts/", "perfwatch/packaging/")):
            return set(CHECKS)
        if path.startswith("perfwatch/python/"):
            checks.update(("backend", "quality"))
        if path.startswith("perfwatch/cpp/") or path == "perfwatch/python/pyproject.toml":
            checks.update(("backend", "native"))
        if path.startswith("perfwatch/ui/dashboard/"):
            checks.add("frontend")
        if path == "perfwatch/.pre-commit-config.yaml":
            checks.add("quality")
    return checks


if __name__ == "__main__":
    base = os.environ["BASE_SHA"]
    if base == "0" * 40:
        base = subprocess.check_output(
            ["git", "hash-object", "-t", "tree", "--stdin"], input="", text=True
        ).strip()
    paths = subprocess.check_output(
        ["git", "diff", "--name-only", "--no-renames", "-z", base, "HEAD"], text=True
    ).split("\0")
    selected = checks_for_paths(paths)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        for check in CHECKS:
            output.write(f"{check}={str(check in selected).lower()}\n")
