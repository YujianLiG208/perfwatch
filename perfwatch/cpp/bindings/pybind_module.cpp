#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "perfwatch/collector.hpp"

namespace py = pybind11;

namespace {

py::dict snapshot_to_dict(const perfwatch::SystemSnapshot& snapshot) {
    py::list processes;
    for (const auto& process : snapshot.top_processes) {
        py::dict process_dict;
        process_dict["pid"] = process.pid;
        process_dict["name"] = process.name;
        process_dict["cpu_percent"] = process.cpu_percent;
        process_dict["rss_bytes"] = process.rss_bytes;
        process_dict["vram_bytes"] = process.vram_bytes;
        process_dict["estimated_power_score"] = process.estimated_power_score;
        processes.append(process_dict);
    }

    py::dict cpu;
    cpu["usage_percent"] = snapshot.cpu.usage_percent;
    cpu["frequency_mhz"] = snapshot.cpu.frequency_mhz;
    cpu["package_power_watts"] = snapshot.cpu.package_power_watts;
    cpu["temperature_celsius"] = snapshot.cpu.temperature_celsius;

    py::dict memory;
    memory["total_bytes"] = snapshot.memory.total_bytes;
    memory["used_bytes"] = snapshot.memory.used_bytes;

    py::dict battery;
    battery["available"] = snapshot.battery.available;
    battery["charging"] = snapshot.battery.charging;
    battery["percent"] = snapshot.battery.percent;
    battery["power_watts"] = snapshot.battery.power_watts;
    battery["energy_remaining_wh"] = snapshot.battery.energy_remaining_wh;

    py::dict gpu;
    gpu["available"] = snapshot.gpu.available;
    gpu["vendor"] = snapshot.gpu.vendor;
    gpu["usage_percent"] = snapshot.gpu.usage_percent;
    gpu["vram_total_bytes"] = snapshot.gpu.vram_total_bytes;
    gpu["vram_used_bytes"] = snapshot.gpu.vram_used_bytes;
    gpu["power_watts"] = snapshot.gpu.power_watts;
    gpu["temperature_celsius"] = snapshot.gpu.temperature_celsius;

    py::dict result;
    result["timestamp_ms"] = snapshot.timestamp_ms;
    result["cpu"] = cpu;
    result["memory"] = memory;
    result["battery"] = battery;
    result["gpu"] = gpu;
    result["top_processes"] = processes;
    return result;
}

}  // namespace

PYBIND11_MODULE(perfwatch_native, module) {
    module.doc() = "Phase 1 perfwatch native mock bindings.";
    module.def(
        "get_mock_snapshot",
        [](std::uint64_t sample_index) {
            return snapshot_to_dict(perfwatch::make_mock_snapshot(sample_index));
        },
        py::arg("sample_index") = 0
    );
}
