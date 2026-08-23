#pragma once

#include <cstdint>

#include "perfwatch/snapshot.hpp"

namespace perfwatch {

class Collector {
public:
    virtual ~Collector() = default;
    virtual SystemSnapshot collect() = 0;
};

class MockCollector final : public Collector {
public:
    SystemSnapshot collect() override;

private:
    std::uint64_t sample_index_{0};
};

SystemSnapshot make_mock_snapshot(std::uint64_t sample_index = 0);

}  // namespace perfwatch
