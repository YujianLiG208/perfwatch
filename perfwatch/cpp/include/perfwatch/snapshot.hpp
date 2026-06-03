#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace perfwatch {

struct CpuSample {
    double usage_percent;
    double frequency_mhz;
    double package_power_watts;
    double temperature_celsius;
};

struct MemorySample {
    std::uint64_t total_bytes;
    std::uint64_t used_bytes;
};

struct BatterySample {
    bool available;
    bool charging;
    double percent;
    double power_watts;
    double energy_remaining_wh;
};

struct GpuSample {
    bool available;
    std::string vendor;
    double usage_percent;
    std::uint64_t vram_total_bytes;
    std::uint64_t vram_used_bytes;
    double power_watts;
    double temperature_celsius;
};

struct ProcessSample {
    int pid;
    std::string name;
    double cpu_percent;
    std::uint64_t rss_bytes;
    std::uint64_t vram_bytes;
    double estimated_power_score;
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
