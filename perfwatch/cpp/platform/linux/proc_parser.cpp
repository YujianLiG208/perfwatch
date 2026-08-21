#include "perfwatch/linux/proc_parser.hpp"

#include <algorithm>
#include <cctype>
#include <sstream>
#include <string>
#include <vector>

// Future long-term plan for Linux: this parser remains fixture-only until live Linux hardware
// and a dedicated validation environment are available.
namespace perfwatch::platform_linux {

namespace {

std::string trim(std::string_view value) {
    auto begin = value.begin();
    auto end = value.end();
    while (begin != end &&
           std::isspace(static_cast<unsigned char>(*begin)) != 0) {
        ++begin;
    }
    while (begin != end &&
           std::isspace(static_cast<unsigned char>(*(end - 1))) != 0) {
        --end;
    }
    return std::string(begin, end);
}

std::optional<std::uint64_t> parse_u64(const std::string& value) {
    try {
        std::size_t consumed = 0;
        const auto parsed = std::stoull(value, &consumed, 10);
        if (consumed != value.size()) {
            return std::nullopt;
        }
        return static_cast<std::uint64_t>(parsed);
    } catch (...) {
        return std::nullopt;
    }
}

std::optional<std::int64_t> parse_i64(const std::string& value) {
    try {
        std::size_t consumed = 0;
        const auto parsed = std::stoll(value, &consumed, 10);
        if (consumed != value.size()) {
            return std::nullopt;
        }
        return static_cast<std::int64_t>(parsed);
    } catch (...) {
        return std::nullopt;
    }
}

std::vector<std::string> split_words(std::string_view value) {
    std::vector<std::string> words;
    std::istringstream stream{std::string(value)};
    std::string word;
    while (stream >> word) {
        words.push_back(word);
    }
    return words;
}

std::optional<std::uint64_t> kib_to_bytes(const std::string& value) {
    const auto kib = parse_u64(value);
    if (!kib) {
        return std::nullopt;
    }
    return *kib * 1024ULL;
}

}  // namespace

std::uint64_t ProcCpuTimes::idle_all() const {
    return idle + iowait;
}

std::uint64_t ProcCpuTimes::total() const {
    return user + nice + system + idle + iowait + irq + softirq + steal;
}

std::optional<ProcCpuTimes> parse_proc_stat_cpu(std::string_view contents) {
    std::istringstream lines{std::string(contents)};
    std::string line;
    while (std::getline(lines, line)) {
        const auto stripped = trim(line);
        if (stripped.rfind("cpu ", 0) != 0) {
            continue;
        }

        const auto fields = split_words(stripped);
        if (fields.size() < 5 || fields[0] != "cpu") {
            return std::nullopt;
        }

        std::vector<std::uint64_t> values;
        values.reserve(fields.size() - 1);
        for (std::size_t i = 1; i < fields.size(); ++i) {
            const auto parsed = parse_u64(fields[i]);
            if (!parsed) {
                return std::nullopt;
            }
            values.push_back(*parsed);
        }

        ProcCpuTimes times;
        times.user = values[0];
        times.nice = values[1];
        times.system = values[2];
        times.idle = values[3];
        if (values.size() > 4) {
            times.iowait = values[4];
        }
        if (values.size() > 5) {
            times.irq = values[5];
        }
        if (values.size() > 6) {
            times.softirq = values[6];
        }
        if (values.size() > 7) {
            times.steal = values[7];
        }
        if (values.size() > 8) {
            times.guest = values[8];
        }
        if (values.size() > 9) {
            times.guest_nice = values[9];
        }
        return times;
    }

    return std::nullopt;
}

std::optional<double> compute_cpu_usage_ratio(const ProcCpuTimes& previous,
                                              const ProcCpuTimes& current) {
    const auto previous_total = previous.total();
    const auto current_total = current.total();
    const auto previous_idle = previous.idle_all();
    const auto current_idle = current.idle_all();

    if (current_total <= previous_total || current_idle < previous_idle) {
        return std::nullopt;
    }

    const auto total_delta = current_total - previous_total;
    const auto idle_delta = current_idle - previous_idle;
    if (total_delta == 0 || idle_delta > total_delta) {
        return std::nullopt;
    }

    auto usage = 1.0 - (static_cast<double>(idle_delta) /
                        static_cast<double>(total_delta));
    usage = std::max(0.0, std::min(1.0, usage));
    return usage;
}

ProcMemInfo parse_proc_meminfo(std::string_view contents) {
    ProcMemInfo info;
    std::istringstream lines{std::string(contents)};
    std::string line;
    while (std::getline(lines, line)) {
        const auto separator = line.find(':');
        if (separator == std::string::npos) {
            continue;
        }

        const auto key = line.substr(0, separator);
        const auto fields = split_words(line.substr(separator + 1));
        if (fields.empty()) {
            continue;
        }

        const auto bytes = kib_to_bytes(fields[0]);
        if (!bytes) {
            continue;
        }

        if (key == "MemTotal") {
            info.total_bytes = bytes;
        } else if (key == "MemAvailable") {
            info.mem_available_bytes = bytes;
        } else if (key == "MemFree") {
            info.mem_free_bytes = bytes;
        } else if (key == "Buffers") {
            info.buffers_bytes = bytes;
        } else if (key == "Cached") {
            info.cached_bytes = bytes;
        } else if (key == "SwapTotal") {
            info.swap_total_bytes = bytes;
        } else if (key == "SwapFree") {
            info.swap_free_bytes = bytes;
        }
    }
    return info;
}

std::optional<std::uint64_t> ProcMemInfo::available_bytes() const {
    if (mem_available_bytes) {
        return mem_available_bytes;
    }

    std::uint64_t fallback = 0;
    bool has_fallback = false;
    const std::optional<std::uint64_t> values[] = {
        mem_free_bytes,
        buffers_bytes,
        cached_bytes,
    };
    for (const auto& value : values) {
        if (value) {
            fallback += *value;
            has_fallback = true;
        }
    }

    if (!has_fallback) {
        return std::nullopt;
    }
    if (total_bytes && fallback > *total_bytes) {
        return total_bytes;
    }
    return fallback;
}

std::optional<std::uint64_t> ProcMemInfo::used_bytes() const {
    if (!total_bytes) {
        return std::nullopt;
    }

    const auto available = available_bytes();
    if (!available) {
        return std::nullopt;
    }
    if (*available >= *total_bytes) {
        return 0ULL;
    }
    return *total_bytes - *available;
}

std::optional<ProcPidStat> parse_proc_pid_stat(std::string_view contents) {
    const auto text = trim(contents);
    const auto open = text.find('(');
    const auto close = text.rfind(')');
    if (open == std::string::npos || close == std::string::npos ||
        close <= open) {
        return std::nullopt;
    }

    const auto pid_text = trim(std::string_view(text).substr(0, open));
    const auto pid = parse_i64(pid_text);
    if (!pid || *pid < 0) {
        return std::nullopt;
    }

    const auto tail = trim(std::string_view(text).substr(close + 1));
    const auto fields = split_words(tail);
    if (fields.size() <= 21 || fields[0].empty()) {
        return std::nullopt;
    }

    const auto utime = parse_u64(fields[11]);
    const auto stime = parse_u64(fields[12]);
    const auto starttime = parse_u64(fields[19]);
    const auto rss = parse_i64(fields[21]);
    if (!utime || !stime || !starttime || !rss) {
        return std::nullopt;
    }

    ProcPidStat stat;
    stat.pid = static_cast<int>(*pid);
    stat.comm = text.substr(open + 1, close - open - 1);
    stat.state = fields[0][0];
    stat.utime = *utime;
    stat.stime = *stime;
    stat.starttime = *starttime;
    stat.rss = *rss;
    return stat;
}

bool proc_parser_available() {
    return true;
}

}  // namespace perfwatch::platform_linux
