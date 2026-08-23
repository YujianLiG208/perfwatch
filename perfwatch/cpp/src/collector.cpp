#include "perfwatch/collector.hpp"

namespace {

std::uint64_t triangle(std::uint64_t sample_index, std::uint64_t period) {
    const auto position = sample_index % period;
    const auto half_period = period / 2;
    return position <= half_period ? position : period - position;
}

}  // namespace

namespace perfwatch {

SystemSnapshot make_mock_snapshot(std::uint64_t sample_index) {
    const auto triangle_value = triangle(sample_index, 20);
    const auto battery_triangle = triangle(sample_index, 80);
    const auto wave = static_cast<double>(triangle_value);
    const auto battery_wave = static_cast<double>(battery_triangle);
    const auto battery_position = sample_index % 80;
    return SystemSnapshot{
        1'710'000'000'000LL + static_cast<std::int64_t>(sample_index * 1'000),
        CpuSample{
            42.5 + 1.5 * wave,
            3'600.0 + 20.0 * wave,
            35.0 + 0.8 * wave,
            65.0 + 0.4 * wave,
        },
        MemorySample{
            34'359'738'368ULL,
            17'179'869'184ULL + 67'108'864ULL * triangle_value,
        },
        BatterySample{
            true,
            battery_position > 40,
            78.0 - 0.25 * battery_wave,
            18.5 + 0.3 * wave,
            45.0 - 0.2 * battery_wave,
        },
        GpuSample{false, "unavailable", 0.0, 0ULL, 0ULL, 0.0, 0.0},
        std::vector<ProcessSample>{
            ProcessSample{
                1234,
                "mock_process",
                12.5 + 0.7 * wave,
                268'435'456ULL + 4'194'304ULL * triangle_value,
                0ULL,
                0.42 + 0.01 * wave,
            },
        },
    };
}

SystemSnapshot MockCollector::collect() {
    const auto snapshot = make_mock_snapshot(sample_index_);
    ++sample_index_;
    return snapshot;
}

}  // namespace perfwatch
