#pragma once

#include <optional>
#include <string>
#include <string_view>

namespace perfwatch::platform_linux {

struct PowerSupplyUevent {
    std::string status;
    std::optional<double> capacity_percent;
    std::optional<double> energy_now_wh;
    std::optional<double> energy_full_wh;
    std::optional<double> power_now_watts;
    std::optional<double> charge_now_ah;
    std::optional<double> charge_full_ah;
    std::optional<double> current_now_amps;
    std::optional<double> voltage_now_volts;

    bool available() const;
    bool charging() const;
    std::optional<double> energy_remaining_wh() const;
    std::optional<double> energy_full_capacity_wh() const;
    std::optional<double> power_watts() const;
};

PowerSupplyUevent parse_power_supply_uevent(std::string_view contents);

bool power_supply_parser_available();

}  // namespace perfwatch::platform_linux
