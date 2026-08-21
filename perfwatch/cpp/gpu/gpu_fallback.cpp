#include "gpu_collector.hpp"

namespace perfwatch {

// Future Long-term plan for GPU adapter: retain the unavailable fallback while vendor-specific
// adapters remain outside the near-term roadmap.
GpuSample unavailable_gpu_sample() {
    return GpuSample{false, "unavailable", 0.0, 0ULL, 0ULL, 0.0, 0.0};
}

}  // namespace perfwatch
