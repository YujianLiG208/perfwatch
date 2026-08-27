#include <cassert>

#include "perfwatch/windows_collector.hpp"

void test_windows_process_cpu_delta() {
    const perfwatch::ProcessCpuSample previous{42, 100, 1'000'000, 10'000'000};
    const perfwatch::ProcessCpuSample current{42, 100, 6'000'000, 20'000'000};

    const auto percent = perfwatch::process_cpu_percent(previous, current, 2);
    assert(percent.has_value());
    assert(*percent == 25.0);

    const perfwatch::ProcessCpuSample reused_pid{42, 101, 7'000'000, 30'000'000};
    assert(!perfwatch::process_cpu_percent(current, reused_pid, 2).has_value());
    assert(!perfwatch::process_cpu_percent(current, current, 2).has_value());
}

void test_windows_collector_returns_live_snapshot() {
#ifdef _WIN32
    perfwatch::WindowsCollector collector;
    const auto snapshot = collector.collect();

    assert(snapshot.timestamp_ms > 1'700'000'000'000LL);
    assert(snapshot.timestamp_ms != 1'710'000'000'000LL);
    assert(snapshot.memory.total_bytes.has_value());
    assert(*snapshot.memory.total_bytes > 0);
#endif
}
