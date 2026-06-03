from perfwatch.analytics.battery_forecast import estimate_remaining_seconds


def test_battery_forecast_normal_input() -> None:
    assert estimate_remaining_seconds(45.0, 15.0) == 10800.0


def test_battery_forecast_invalid_input() -> None:
    assert estimate_remaining_seconds(45.0, 0.0) is None
    assert estimate_remaining_seconds(45.0, -1.0) is None
    assert estimate_remaining_seconds(-1.0, 10.0) is None
