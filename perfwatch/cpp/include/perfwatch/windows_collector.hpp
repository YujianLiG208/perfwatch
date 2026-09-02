#pragma once

#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <vector>

#include "perfwatch/snapshot.hpp"

namespace perfwatch {

struct ProcessCpuSample {
    std::uint32_t pid;
    std::uint64_t creation_time_100ns;
    std::uint64_t cpu_time_100ns;
    std::uint64_t wall_time_100ns;
};

std::optional<double> process_cpu_percent(
    const ProcessCpuSample& previous,
    const ProcessCpuSample& current,
    std::uint32_t logical_processors
);

struct CollectionIssue {
    std::string code;
    std::string message;
};

class WindowsCollector final {
public:
    WindowsCollector();
    ~WindowsCollector();
    SystemSnapshot collect();
    const std::vector<CollectionIssue>& collection_issues() const;

private:
    struct State;
    std::unique_ptr<State> state_;
    std::vector<CollectionIssue> issues_;
};

}  // namespace perfwatch
