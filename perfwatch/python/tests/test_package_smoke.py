import os
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace

import pytest


def test_package_smoke_isolates_and_cleans_data_after_child_failure(tmp_path, monkeypatch) -> None:
    smoke = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "scripts" / "smoke_windows_package.py")
    )
    user_data = tmp_path / "user-data"
    user_data.mkdir()
    history = user_data / "perfwatch.sqlite3"
    history.write_text("existing history", encoding="utf-8")
    monkeypatch.setenv("LOCALAPPDATA", str(user_data))
    monkeypatch.setattr(sys, "argv", ["smoke", "--executable", sys.executable])
    monkeypatch.setitem(smoke["main"].__globals__, "_unused_port", lambda host: 8000)
    monkeypatch.setattr(smoke["subprocess"], "CREATE_NEW_PROCESS_GROUP", 0, raising=False)
    temporary_roots = []

    def start_child(command, **kwargs):
        data_root = Path(kwargs.get("env", os.environ)["LOCALAPPDATA"])
        assert data_root != user_data
        temporary_roots.append(data_root)
        database = data_root / "PerfWatch" / "perfwatch.sqlite3"
        database.parent.mkdir()
        database.write_text("mock sample", encoding="utf-8")
        return SimpleNamespace(poll=lambda: 1, returncode=1)

    monkeypatch.setattr(smoke["subprocess"], "Popen", start_child)
    with pytest.raises(RuntimeError, match="application exited early"):
        smoke["main"]()

    assert len(temporary_roots) == 1
    assert not temporary_roots[0].exists()
    assert history.read_text(encoding="utf-8") == "existing history"
