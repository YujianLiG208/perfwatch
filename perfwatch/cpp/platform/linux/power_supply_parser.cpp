namespace perfwatch::platform_linux {

bool power_supply_parser_available() {
    // TODO(phase 2): parse fixture-backed /sys/class/power_supply samples.
    return false;
}

}  // namespace perfwatch::platform_linux
