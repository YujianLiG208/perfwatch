from perfwatch.analytics.process_energy_score import estimate_process_power_score


def test_process_energy_score_is_deterministic() -> None:
    first = estimate_process_power_score(12.5, 268435456)
    second = estimate_process_power_score(12.5, 268435456)

    assert first == second
    assert first > 0
