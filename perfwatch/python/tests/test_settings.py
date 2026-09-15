from pathlib import Path

import pytest

from perfwatch.config.settings import get_settings


def test_settings_read_phase_four_environment_variables(monkeypatch) -> None:
    monkeypatch.setenv("PERFWATCH_DATABASE_PATH", "custom.sqlite3")
    monkeypatch.setenv("PERFWATCH_SAMPLE_INTERVAL_SECONDS", "2.5")
    monkeypatch.setenv("PERFWATCH_USE_MOCK_COLLECTOR", "true")

    settings = get_settings()

    assert settings.database_path == Path("custom.sqlite3")
    assert settings.snapshot_interval_seconds == 2.5
    assert settings.use_mock_collector is True


def test_boolean_setting_preserves_normalization_default_and_error(monkeypatch) -> None:
    name = "PERFWATCH_USE_MOCK_COLLECTOR"
    monkeypatch.delenv(name, raising=False)
    assert get_settings().use_mock_collector is False

    monkeypatch.setenv(name, " YES ")
    assert get_settings().use_mock_collector is True
    monkeypatch.setenv(name, " Off ")
    assert get_settings().use_mock_collector is False

    monkeypatch.setenv(name, "maybe")
    with pytest.raises(ValueError, match=f"^{name} must be a boolean value$"):
        get_settings()
