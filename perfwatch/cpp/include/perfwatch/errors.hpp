#pragma once

#include <stdexcept>
#include <string>

namespace perfwatch {

class PerfwatchError : public std::runtime_error {
public:
    explicit PerfwatchError(const std::string& message)
        : std::runtime_error(message) {}
};

}  // namespace perfwatch
