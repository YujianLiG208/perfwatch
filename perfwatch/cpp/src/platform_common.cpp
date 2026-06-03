#include "perfwatch/platform.hpp"

namespace perfwatch {

Platform current_platform() {
#if defined(_WIN32)
    return Platform::Windows;
#elif defined(__linux__)
    return Platform::Linux;
#else
    return Platform::Unknown;
#endif
}

}  // namespace perfwatch
