namespace perfwatch::platform_windows {

bool wmi_fallback_available() {
    // TODO(phase 2): add WMI fallback only after the interface is tested.
    return false;
}

}  // namespace perfwatch::platform_windows
