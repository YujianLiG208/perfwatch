// Future long-term plan for Linux: retain this compile-safe boundary until live Linux hardware
// and a dedicated validation environment are available.
namespace perfwatch::platform_linux {

bool linux_collector_available() {
    return false;
}

}  // namespace perfwatch::platform_linux
