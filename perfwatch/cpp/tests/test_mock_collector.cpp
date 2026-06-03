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

    perfwatch::MockCollector collector;
    const auto first = collector.collect();
    const auto second = collector.collect();

    assert(first.timestamp_ms == second.timestamp_ms);
    assert(first.cpu.usage_percent == second.cpu.usage_percent);
    assert(first.memory.used_bytes == second.memory.used_bytes);
    assert(first.top_processes[0].estimated_power_score ==
           second.top_processes[0].estimated_power_score);

    return 0;
}
