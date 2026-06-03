#include "perfwatch/linux/power_supply_parser.hpp"

#include <cctype>
#include <sstream>
#include <string>
#include <unordered_map>

namespace perfwatch::platform_linux {

namespace {

std::string trim(std::string_view value) {
    auto begin = value.begin();
    auto end = value.end();
    while (begin != end &&
           std::isspace(static_cast<unsigned char>(*begin)) != 0) {
        ++begin;
    }
    while (begin != end &&
           std::isspace(static_cast<unsigned char>(*(end - 1))) != 0) {
        --end;
    }
    return std::string(begin, end);
}

std::optional<double> parse_double(const std::string& value) {
    try {
        std::size_t consumed = 0;
        const auto parsed = std::stod(value, &consumed);
        if (consumed != value.size()) {
            return std::nullopt;
        }
        return parsed;
    } catch (...) {
        return std::nullopt;
    }
}

std::optional<double> parse_scaled(
    const std::unordered_map<std::string, std::string>& values,
    const std::string& key,
    double scale) {
    const auto found = values.find(key);
    if (found == values.end()) {
        return std::nullopt;
    }
    const auto parsed = parse_double(found->second);
    if (!parsed) {
        return std::nullopt;
    }
    return *parsed / scale;
}

std::unordered_map<std::string, std::string> parse_key_values(
    std::string_view contents) {
    std::unordered_map<std::string, std::string> values;
    std::istringstream lines{std::string(contents)};
    std::string line;
    while (std::getline(lines, line)) {
        const auto stripped = trim(line);
        const auto separator = stripped.find('=');
        if (separator == std::string::npos) {
            continue;
        }
        values[stripped.substr(0, separator)] = stripped.substr(separator + 1);
    }
    return values;
}

}  // namespace

bool PowerSupplyUevent::available() const {
    return !status.empty() || capacity_percent || energy_now_wh ||
           energy_full_wh || power_now_watts || charge_now_ah ||
           charge_full_ah || current_now_amps || voltage_now_volts;
}

bool PowerSupplyUevent::charging() const {
    return status == "Charging";
}

std::optional<double> PowerSupplyUevent::energy_remaining_wh() const {
    if (energy_now_wh) {
        return energy_now_wh;
    }
    if (charge_now_ah && voltage_now_volts) {
        return *charge_now_ah * *voltage_now_volts;
    }
    return std::nullopt;
}

std::optional<double> PowerSupplyUevent::energy_full_capacity_wh() const {
    if (energy_full_wh) {
        return energy_full_wh;
    }
    if (charge_full_ah && voltage_now_volts) {
        return *charge_full_ah * *voltage_now_volts;
    }
    return std::nullopt;
}

std::optional<double> PowerSupplyUevent::power_watts() const {
    if (power_now_watts) {
        return power_now_watts;
    }
    if (current_now_amps && voltage_now_volts) {
        return *current_now_amps * *voltage_now_volts;
    }
    return std::nullopt;
}

PowerSupplyUevent parse_power_supply_uevent(std::string_view contents) {
    const auto values = parse_key_values(contents);

    PowerSupplyUevent event;
    const auto status = values.find("POWER_SUPPLY_STATUS");
    if (status != values.end()) {
        event.status = status->second;
    }

    event.capacity_percent =
        parse_scaled(values, "POWER_SUPPLY_CAPACITY", 1.0);
    event.energy_now_wh =
        parse_scaled(values, "POWER_SUPPLY_ENERGY_NOW", 1000000.0);
    event.energy_full_wh =
        parse_scaled(values, "POWER_SUPPLY_ENERGY_FULL", 1000000.0);
    event.power_now_watts =
        parse_scaled(values, "POWER_SUPPLY_POWER_NOW", 1000000.0);
    event.charge_now_ah =
        parse_scaled(values, "POWER_SUPPLY_CHARGE_NOW", 1000000.0);
    event.charge_full_ah =
        parse_scaled(values, "POWER_SUPPLY_CHARGE_FULL", 1000000.0);
    event.current_now_amps =
        parse_scaled(values, "POWER_SUPPLY_CURRENT_NOW", 1000000.0);
    event.voltage_now_volts =
        parse_scaled(values, "POWER_SUPPLY_VOLTAGE_NOW", 1000000.0);
    return event;
}

bool power_supply_parser_available() {
    return true;
}

}  // namespace perfwatch::platform_linux
