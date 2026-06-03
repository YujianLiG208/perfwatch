namespace perfwatch::platform_linux {

bool proc_parser_available() {
    // TODO(phase 2): parse fixture-backed /proc samples before reading the host.
    return false;
}

}  // namespace perfwatch::platform_linux
