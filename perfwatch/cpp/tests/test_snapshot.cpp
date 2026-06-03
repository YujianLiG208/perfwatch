#include <cassert>

#include "perfwatch/collector.hpp"

void test_mock_snapshot_shape() {
    const auto snapshot = perfwatch::make_mock_snapshot();

    assert(snapshot.timestamp_ms == 1710000000000LL);
    assert(snapshot.cpu.usage_percent == 42.5);
    assert(snapshot.memory.total_bytes == 34359738368ULL);
    assert(snapshot.battery.available);
    assert(!snapshot.battery.charging);
    assert(snapshot.gpu.available == false);
    assert(snapshot.gpu.vendor == "unavailable");
    assert(snapshot.top_processes.size() == 1);
    assert(snapshot.top_processes[0].name == "mock_process");
}
