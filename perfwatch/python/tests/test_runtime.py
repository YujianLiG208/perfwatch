from perfwatch import runtime


def test_runtime_paths_and_frozen_child_command(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(runtime.sys, "frozen", True, raising=False)
    monkeypatch.setattr(runtime.sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    monkeypatch.setattr(runtime.sys, "executable", str(tmp_path / "perfwatch.exe"))

    assert runtime.default_data_directory() == tmp_path / "PerfWatch"
    assert runtime.bundle_root() == tmp_path / "bundle"
    assert runtime.self_command() == [str(tmp_path / "perfwatch.exe")]
