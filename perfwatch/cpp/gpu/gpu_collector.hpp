#pragma once

#include "perfwatch/snapshot.hpp"

namespace perfwatch {

class GpuCollector {
public:
    virtual ~GpuCollector() = default;
    virtual GpuSample collect() = 0;
};

GpuSample unavailable_gpu_sample();

}  // namespace perfwatch
