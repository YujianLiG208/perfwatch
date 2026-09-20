from pathlib import Path
import runpy


def test_ci_scope_selects_checks_for_changed_product_boundaries() -> None:
    checks_for_paths = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "scripts" / "ci_scope.py")
    )["checks_for_paths"]

    assert checks_for_paths(["README.md", "perfwatch/ui/dashboard/README.md"]) == set()
    assert checks_for_paths(["perfwatch/ui/dashboard/src/App.tsx"]) == {"frontend"}
    assert checks_for_paths(["perfwatch/python/tests/test_api.py"]) == {"backend", "quality"}
    assert checks_for_paths([
        "perfwatch/cpp/tests/test_windows_collector.cpp",
        "perfwatch/python/pyproject.toml",
    ]) == {"backend", "native", "quality"}
    assert checks_for_paths([".github/workflows/ci.yml"]) == {
        "backend", "native", "frontend", "quality"
    }
