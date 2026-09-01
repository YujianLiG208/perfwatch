#include <algorithm>
#include <chrono>
#include <cstdint>
#include <limits>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "perfwatch/errors.hpp"
#include "perfwatch/windows_collector.hpp"

#ifdef _WIN32
#define NOMINMAX
#include <windows.h>

#include <pdh.h>
#include <PdhMsg.h>
#include <powrprof.h>
#include <psapi.h>
#endif

namespace {

#ifdef _WIN32

struct ProcessorPowerInformation {
    ULONG number;
    ULONG max_mhz;
    ULONG current_mhz;
    ULONG mhz_limit;
    ULONG max_idle_state;
    ULONG current_idle_state;
};

constexpr ULONG kBatteryUnknownRate = 0x80000000UL;

std::uint64_t filetime_value(const FILETIME& value) {
    ULARGE_INTEGER result{};
    result.LowPart = value.dwLowDateTime;
    result.HighPart = value.dwHighDateTime;
    return result.QuadPart;
}

std::string process_name(HANDLE process) {
    std::vector<wchar_t> path(1024);
    DWORD length = static_cast<DWORD>(path.size());
    if (!QueryFullProcessImageNameW(process, 0, path.data(), &length)) {
        return "unknown";
    }

    const std::wstring full_path(path.data(), length);
    const auto separator = full_path.find_last_of(L"\\/");
    const auto name = full_path.substr(separator == std::wstring::npos ? 0 : separator + 1);
    const auto utf8_size = WideCharToMultiByte(
        CP_UTF8, 0, name.data(), static_cast<int>(name.size()), nullptr, 0, nullptr, nullptr
    );
    if (utf8_size <= 0) {
        return "unknown";
    }

    std::string utf8(static_cast<std::size_t>(utf8_size), '\0');
    WideCharToMultiByte(
        CP_UTF8,
        0,
        name.data(),
        static_cast<int>(name.size()),
        utf8.data(),
        utf8_size,
        nullptr,
        nullptr
    );
    return utf8;
}

#endif

}  // namespace

namespace perfwatch {

std::optional<double> process_cpu_percent(
    const ProcessCpuSample& previous,
    const ProcessCpuSample& current,
    std::uint32_t logical_processors
) {
    if (logical_processors == 0 || previous.pid != current.pid ||
        previous.creation_time_100ns != current.creation_time_100ns ||
        current.cpu_time_100ns <= previous.cpu_time_100ns ||
        current.wall_time_100ns <= previous.wall_time_100ns) {
        return std::nullopt;
    }

    const auto cpu_delta = current.cpu_time_100ns - previous.cpu_time_100ns;
    const auto wall_delta = current.wall_time_100ns - previous.wall_time_100ns;
    const auto percent = 100.0 * static_cast<double>(cpu_delta) /
        (static_cast<double>(wall_delta) * logical_processors);
    return std::clamp(percent, 0.0, 100.0);
}

struct WindowsCollector::State {
#ifdef _WIN32
    PDH_HQUERY cpu_query{nullptr};
    PDH_HCOUNTER cpu_counter{nullptr};
    bool cpu_primed{false};
    std::unordered_map<std::uint32_t, ProcessCpuSample> process_baselines;

    State() {
        if (PdhOpenQueryW(nullptr, 0, &cpu_query) != ERROR_SUCCESS ||
            PdhAddEnglishCounterW(
                cpu_query,
                L"\\Processor(_Total)\\% Processor Time",
                0,
                &cpu_counter
            ) != ERROR_SUCCESS) {
            if (cpu_query != nullptr) {
                PdhCloseQuery(cpu_query);
            }
            cpu_query = nullptr;
            cpu_counter = nullptr;
        }
    }

    ~State() {
        if (cpu_query != nullptr) {
            PdhCloseQuery(cpu_query);
        }
    }
#endif
};

WindowsCollector::WindowsCollector() : state_(std::make_unique<State>()) {}

WindowsCollector::~WindowsCollector() = default;

const std::vector<CollectionIssue>& WindowsCollector::collection_issues() const {
    return issues_;
}

SystemSnapshot WindowsCollector::collect() {
#ifndef _WIN32
    throw PerfwatchError("live Windows collection is unavailable on this platform");
#else
    issues_.clear();
    SystemSnapshot snapshot{};
    snapshot.timestamp_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()
    ).count();
    snapshot.gpu.available = false;
    snapshot.gpu.vendor = "unavailable";

    if (state_->cpu_query == nullptr || state_->cpu_counter == nullptr) {
        issues_.push_back({"cpu_usage_unavailable", "PDH total CPU counter is unavailable"});
    } else if (PdhCollectQueryData(state_->cpu_query) != ERROR_SUCCESS) {
        issues_.push_back({"cpu_usage_unavailable", "PDH total CPU collection failed"});
    } else if (!state_->cpu_primed) {
        state_->cpu_primed = true;
    } else {
        PDH_FMT_COUNTERVALUE value{};
        DWORD type = 0;
        const auto status = PdhGetFormattedCounterValue(
            state_->cpu_counter, PDH_FMT_DOUBLE, &type, &value
        );
        if (status == ERROR_SUCCESS &&
            (value.CStatus == PDH_CSTATUS_VALID_DATA ||
             value.CStatus == PDH_CSTATUS_NEW_DATA)) {
            snapshot.cpu.usage_percent = std::clamp(value.doubleValue, 0.0, 100.0);
        } else {
            issues_.push_back({"cpu_usage_unavailable", "PDH total CPU value is invalid"});
        }
    }

    const auto processor_count = GetActiveProcessorCount(ALL_PROCESSOR_GROUPS);
    if (processor_count > 0) {
        std::vector<ProcessorPowerInformation> power_information(processor_count);
        if (CallNtPowerInformation(
                ProcessorInformation,
                nullptr,
                0,
                power_information.data(),
                static_cast<ULONG>(power_information.size() * sizeof(power_information[0]))
            ) == ERROR_SUCCESS) {
            std::uint64_t total_mhz = 0;
            std::uint32_t valid_processors = 0;
            for (const auto& information : power_information) {
                if (information.current_mhz > 0) {
                    total_mhz += information.current_mhz;
                    ++valid_processors;
                }
            }
            if (valid_processors > 0) {
                snapshot.cpu.frequency_mhz =
                    static_cast<double>(total_mhz) / valid_processors;
            }
        }
    }
    if (!snapshot.cpu.frequency_mhz.has_value()) {
        issues_.push_back({"cpu_frequency_unavailable", "processor frequency is unavailable"});
    }
    issues_.push_back({"cpu_power_unavailable", "CPU package power is unavailable"});
    issues_.push_back({"cpu_temperature_unavailable", "CPU temperature is unavailable"});

    MEMORYSTATUSEX memory{sizeof(memory)};
    if (GlobalMemoryStatusEx(&memory)) {
        snapshot.memory.total_bytes = memory.ullTotalPhys;
        snapshot.memory.used_bytes = memory.ullTotalPhys - memory.ullAvailPhys;
    } else {
        issues_.push_back({"memory_unavailable", "physical memory status is unavailable"});
    }

    SYSTEM_POWER_STATUS power_status{};
    const auto has_power_status = GetSystemPowerStatus(&power_status) != FALSE;
    SYSTEM_BATTERY_STATE battery_state{};
    const auto has_battery_state = CallNtPowerInformation(
        SystemBatteryState, nullptr, 0, &battery_state, sizeof(battery_state)
    ) == ERROR_SUCCESS;

    if (has_battery_state) {
        snapshot.battery.available = battery_state.BatteryPresent != FALSE;
    } else if (has_power_status) {
        snapshot.battery.available =
            power_status.BatteryFlag != 128 && power_status.BatteryFlag != 255;
    } else {
        issues_.push_back({"battery_unavailable", "battery status is unavailable"});
    }

    if (snapshot.battery.available) {
        if (has_battery_state) {
            snapshot.battery.charging = battery_state.Charging != FALSE;
            if (battery_state.RemainingCapacity > 0 &&
                battery_state.RemainingCapacity != std::numeric_limits<ULONG>::max()) {
                snapshot.battery.energy_remaining_wh =
                    static_cast<double>(battery_state.RemainingCapacity) / 1000.0;
            }
            if (battery_state.Rate != 0 &&
                battery_state.Rate != kBatteryUnknownRate &&
                battery_state.Rate != std::numeric_limits<ULONG>::max()) {
                const auto signed_rate = static_cast<std::int64_t>(
                    static_cast<LONG>(battery_state.Rate)
                );
                snapshot.battery.power_watts =
                    static_cast<double>(signed_rate < 0 ? -signed_rate : signed_rate) / 1000.0;
            }
        } else if (has_power_status) {
            snapshot.battery.charging = (power_status.BatteryFlag & 8) != 0;
        }

        if (has_power_status && power_status.BatteryLifePercent <= 100) {
            snapshot.battery.percent = power_status.BatteryLifePercent;
        }
    }

    FILETIME wall_filetime{};
    GetSystemTimeAsFileTime(&wall_filetime);
    const auto wall_time = filetime_value(wall_filetime);
    std::vector<DWORD> pids(1024);
    DWORD bytes_returned = 0;
    while (EnumProcesses(
        pids.data(), static_cast<DWORD>(pids.size() * sizeof(DWORD)), &bytes_returned
    )) {
        if (bytes_returned < pids.size() * sizeof(DWORD)) {
            break;
        }
        pids.resize(pids.size() * 2);
    }

    if (bytes_returned == 0) {
        issues_.push_back({"processes_unavailable", "process enumeration is unavailable"});
    } else {
        pids.resize(bytes_returned / sizeof(DWORD));
        std::unordered_map<std::uint32_t, ProcessCpuSample> next_baselines;
        for (const auto pid : pids) {
            if (pid == 0) {
                continue;
            }

            HANDLE process = OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ, FALSE, pid
            );
            if (process == nullptr) {
                continue;
            }

            FILETIME creation{}, exit{}, kernel{}, user{};
            PROCESS_MEMORY_COUNTERS_EX memory_counters{};
            const auto times_ok = GetProcessTimes(process, &creation, &exit, &kernel, &user) != FALSE;
            const auto memory_ok = GetProcessMemoryInfo(
                process,
                reinterpret_cast<PROCESS_MEMORY_COUNTERS*>(&memory_counters),
                sizeof(memory_counters)
            ) != FALSE;
            const auto name = process_name(process);
            CloseHandle(process);
            if (!times_ok || !memory_ok) {
                continue;
            }

            const ProcessCpuSample current{
                pid,
                filetime_value(creation),
                filetime_value(kernel) + filetime_value(user),
                wall_time,
            };
            next_baselines.emplace(pid, current);
            std::optional<double> cpu_percent;
            const auto previous = state_->process_baselines.find(pid);
            if (previous != state_->process_baselines.end()) {
                cpu_percent = process_cpu_percent(previous->second, current, processor_count);
            }
            snapshot.top_processes.push_back(ProcessSample{
                static_cast<int>(pid),
                name,
                cpu_percent,
                static_cast<std::uint64_t>(memory_counters.WorkingSetSize),
                std::nullopt,
                std::nullopt,
            });
        }
        state_->process_baselines = std::move(next_baselines);
        std::sort(
            snapshot.top_processes.begin(),
            snapshot.top_processes.end(),
            [](const ProcessSample& left, const ProcessSample& right) {
                if (left.cpu_percent.has_value() != right.cpu_percent.has_value()) {
                    return left.cpu_percent.has_value();
                }
                if (left.cpu_percent != right.cpu_percent) {
                    return left.cpu_percent > right.cpu_percent;
                }
                return left.rss_bytes > right.rss_bytes;
            }
        );
        if (snapshot.top_processes.size() > 10) {
            snapshot.top_processes.resize(10);
        }
    }

    return snapshot;
#endif
}

}  // namespace perfwatch
