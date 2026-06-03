#include "perfwatch/collector.hpp"

namespace perfwatch {

SystemSnapshot make_mock_snapshot() {
    return SystemSnapshot{
        1710000000000LL,
        CpuSample{42.5, 3600.0, 35.0, 65.0},
        MemorySample{34359738368ULL, 17179869184ULL},
        BatterySample{true, false, 78.0, 18.5, 45.0},
        GpuSample{false, "unavailable", 0.0, 0ULL, 0ULL, 0.0, 0.0},
        std::vector<ProcessSample>{
            ProcessSample{1234, "mock_process", 12.5, 268435456ULL, 0ULL, 0.42},
        },
    };
}

SystemSnapshot MockCollector::collect() {
    return make_mock_snapshot();
}

}  // namespace perfwatch
