#pragma once

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
};

SystemSnapshot make_mock_snapshot();

}  // namespace perfwatch
