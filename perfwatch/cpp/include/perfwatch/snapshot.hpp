#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace perfwatch {

struct CpuSample {
    std::optional<double> usage_percent;
    std::optional<double> frequency_mhz;
    std::optional<double> package_power_watts;
    std::optional<double> temperature_celsius;
};

struct MemorySample {
    std::optional<std::uint64_t> total_bytes;
    std::optional<std::uint64_t> used_bytes;
};

struct BatterySample {
    bool available;
    std::optional<bool> charging;
    std::optional<double> percent;
    std::optional<double> power_watts;
    std::optional<double> energy_remaining_wh;
};

struct GpuSample {
    bool available;
    std::string vendor;
    std::optional<double> usage_percent;
    std::optional<std::uint64_t> vram_total_bytes;
    std::optional<std::uint64_t> vram_used_bytes;
    std::optional<double> power_watts;
    std::optional<double> temperature_celsius;
};

struct ProcessSample {
    int pid;
    std::string name;
    std::optional<double> cpu_percent;
    std::optional<std::uint64_t> rss_bytes;
    std::optional<std::uint64_t> vram_bytes;
    std::optional<double> estimated_power_score;
};

struct SystemSnapshot {
    std::int64_t timestamp_ms;
    CpuSample cpu;
    MemorySample memory;
    BatterySample battery;
    GpuSample gpu;
    std::vector<ProcessSample> top_processes;
};

}  // namespace perfwatch
