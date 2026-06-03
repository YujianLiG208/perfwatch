#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace perfwatch::platform_linux {

struct ProcCpuTimes {
    std::uint64_t user = 0;
    std::uint64_t nice = 0;
    std::uint64_t system = 0;
    std::uint64_t idle = 0;
    std::uint64_t iowait = 0;
    std::uint64_t irq = 0;
    std::uint64_t softirq = 0;
    std::uint64_t steal = 0;
    std::uint64_t guest = 0;
    std::uint64_t guest_nice = 0;

    std::uint64_t idle_all() const;
    std::uint64_t total() const;
};

struct ProcMemInfo {
    std::optional<std::uint64_t> total_bytes;
    std::optional<std::uint64_t> mem_available_bytes;
    std::optional<std::uint64_t> mem_free_bytes;
    std::optional<std::uint64_t> buffers_bytes;
    std::optional<std::uint64_t> cached_bytes;
    std::optional<std::uint64_t> swap_total_bytes;
    std::optional<std::uint64_t> swap_free_bytes;

    std::optional<std::uint64_t> available_bytes() const;
    std::optional<std::uint64_t> used_bytes() const;
};

struct ProcPidStat {
    int pid = 0;
    std::string comm;
    char state = '\0';
    std::uint64_t utime = 0;
    std::uint64_t stime = 0;
    std::uint64_t starttime = 0;
    std::int64_t rss = 0;
};

std::optional<ProcCpuTimes> parse_proc_stat_cpu(std::string_view contents);
std::optional<double> compute_cpu_usage_ratio(const ProcCpuTimes& previous,
                                              const ProcCpuTimes& current);
ProcMemInfo parse_proc_meminfo(std::string_view contents);
std::optional<ProcPidStat> parse_proc_pid_stat(std::string_view contents);

bool proc_parser_available();

}  // namespace perfwatch::platform_linux
