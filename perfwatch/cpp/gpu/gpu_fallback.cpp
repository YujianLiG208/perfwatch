#include "gpu_collector.hpp"

namespace perfwatch {

GpuSample unavailable_gpu_sample() {
    // TODO(phase 2+): replace with vendor adapters after CPU/memory paths are stable.
    return GpuSample{false, "unavailable", 0.0, 0ULL, 0ULL, 0.0, 0.0};
}

}  // namespace perfwatch
