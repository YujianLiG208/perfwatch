#pragma once

namespace perfwatch {

enum class Platform {
    Linux,
    Windows,
    Unknown,
};

Platform current_platform();

}  // namespace perfwatch
