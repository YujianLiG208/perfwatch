#include <cassert>

#include "perfwatch/collector.hpp"

void test_mock_snapshot_shape();

int main() {
    test_mock_snapshot_shape();

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
