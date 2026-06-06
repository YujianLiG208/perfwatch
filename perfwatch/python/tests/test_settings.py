from pathlib import Path

from perfwatch.config.settings import get_settings


def test_settings_read_phase_four_environment_variables(monkeypatch) -> None:
    monkeypatch.setenv("PERFWATCH_DATABASE_PATH", "custom.sqlite3")
    monkeypatch.setenv("PERFWATCH_SAMPLE_INTERVAL_SECONDS", "2.5")
    monkeypatch.setenv("PERFWATCH_USE_MOCK_COLLECTOR", "true")

    settings = get_settings()

    assert settings.database_path == Path("custom.sqlite3")
    assert settings.snapshot_interval_seconds == 2.5
    assert settings.use_mock_collector is True
