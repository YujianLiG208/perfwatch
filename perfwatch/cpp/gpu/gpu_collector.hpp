#pragma once

#include "perfwatch/snapshot.hpp"

namespace perfwatch {

// Future Long-term plan for GPU adapter: keep this interface dormant until suitable hardware and
// repeatable vendor-specific validation are available.
class GpuCollector {
public:
    virtual ~GpuCollector() = default;
    virtual GpuSample collect() = 0;
};

GpuSample unavailable_gpu_sample();

}  // namespace perfwatch
