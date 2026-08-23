#include <cassert>

#include "perfwatch/collector.hpp"

void test_mock_snapshot_shape();
void test_proc_stat_parser();
void test_meminfo_parser();
void test_proc_pid_stat_parser();
void test_power_supply_parser();

int main() {
    test_mock_snapshot_shape();
    test_proc_stat_parser();
    test_meminfo_parser();
    test_proc_pid_stat_parser();
    test_power_supply_parser();

    const auto baseline = perfwatch::make_mock_snapshot(0);
    assert(baseline.timestamp_ms == 1'710'000'000'000);
    assert(baseline.cpu.usage_percent == 42.5);
    assert(baseline.memory.used_bytes == 17'179'869'184ULL);
    assert(baseline.battery.percent == 78.0);
    assert(baseline.top_processes.at(0).estimated_power_score == 0.42);

    const auto indexed = perfwatch::make_mock_snapshot(3);
    assert(indexed.timestamp_ms == 1'710'000'003'000);
    assert(indexed.cpu.usage_percent == 47.0);
    assert(indexed.memory.used_bytes == 17'381'195'776ULL);
    assert(indexed.battery.percent == 77.25);
    assert(indexed.top_processes.at(0).rss_bytes == 281'018'368ULL);

    const auto repeated = perfwatch::make_mock_snapshot(3);
    assert(indexed.timestamp_ms == repeated.timestamp_ms);
    assert(indexed.cpu.usage_percent == repeated.cpu.usage_percent);
    assert(indexed.memory.used_bytes == repeated.memory.used_bytes);
    assert(indexed.battery.percent == repeated.battery.percent);
    assert(indexed.top_processes.at(0).estimated_power_score ==
           repeated.top_processes.at(0).estimated_power_score);

    const auto peak = perfwatch::make_mock_snapshot(10);
    const auto descending = perfwatch::make_mock_snapshot(11);
    assert(peak.cpu.usage_percent == 57.5);
    assert(descending.cpu.usage_percent == 56.0);
    assert(peak.cpu.usage_percent > descending.cpu.usage_percent);

    const auto last_discharging = perfwatch::make_mock_snapshot(40);
    const auto first_charging = perfwatch::make_mock_snapshot(41);
    const auto next_cycle = perfwatch::make_mock_snapshot(80);
    assert(!last_discharging.battery.charging);
    assert(last_discharging.battery.percent == 68.0);
    assert(first_charging.battery.charging);
    assert(first_charging.battery.percent == 68.25);
    assert(!next_cycle.battery.charging);
    assert(next_cycle.battery.percent == 78.0);

    perfwatch::MockCollector first_collector;
    perfwatch::MockCollector second_collector;
    assert(first_collector.collect().timestamp_ms == 1'710'000'000'000);
    assert(first_collector.collect().timestamp_ms == 1'710'000'001'000);
    assert(second_collector.collect().timestamp_ms == 1'710'000'000'000);

    return 0;
}
