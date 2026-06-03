#include <cassert>
#include <cmath>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>

#include "perfwatch/linux/power_supply_parser.hpp"

namespace {

std::string read_linux_fixture(const std::string& name) {
    const std::string path =
        std::string(PERFWATCH_TEST_FIXTURE_DIR) + "/" + name;
    std::ifstream input(path);
    if (!input) {
        throw std::runtime_error("Unable to open fixture: " + path);
    }
    std::ostringstream contents;
    contents << input.rdbuf();
    return contents.str();
}

bool nearly_equal(double left, double right) {
    return std::fabs(left - right) < 0.0000001;
}

}  // namespace

void test_power_supply_parser() {
    using perfwatch::platform_linux::parse_power_supply_uevent;

    const auto energy = parse_power_supply_uevent(
        read_linux_fixture("power_supply_uevent_energy_power.txt"));
    assert(energy.available());
    assert(!energy.charging());
    assert(energy.status == "Discharging");
    assert(energy.capacity_percent);
    assert(nearly_equal(*energy.capacity_percent, 78.0));
    assert(energy.energy_now_wh);
    assert(nearly_equal(*energy.energy_now_wh, 45.0));
    assert(energy.energy_full_wh);
    assert(nearly_equal(*energy.energy_full_wh, 58.0));
    assert(energy.power_now_watts);
    assert(nearly_equal(*energy.power_now_watts, 18.5));
    assert(energy.energy_remaining_wh());
    assert(nearly_equal(*energy.energy_remaining_wh(), 45.0));
    assert(energy.power_watts());
    assert(nearly_equal(*energy.power_watts(), 18.5));

    const auto charge = parse_power_supply_uevent(
        read_linux_fixture("power_supply_uevent_charge_current_voltage.txt"));
    assert(charge.available());
    assert(charge.charging());
    assert(charge.status == "Charging");
    assert(charge.charge_now_ah);
    assert(nearly_equal(*charge.charge_now_ah, 3.0));
    assert(charge.charge_full_ah);
    assert(nearly_equal(*charge.charge_full_ah, 4.0));
    assert(charge.current_now_amps);
    assert(nearly_equal(*charge.current_now_amps, 1.2));
    assert(charge.voltage_now_volts);
    assert(nearly_equal(*charge.voltage_now_volts, 11.5));
    assert(charge.energy_remaining_wh());
    assert(nearly_equal(*charge.energy_remaining_wh(), 34.5));
    assert(charge.energy_full_capacity_wh());
    assert(nearly_equal(*charge.energy_full_capacity_wh(), 46.0));
    assert(charge.power_watts());
    assert(nearly_equal(*charge.power_watts(), 13.8));

    const auto missing = parse_power_supply_uevent(
        read_linux_fixture("power_supply_uevent_missing_fields.txt"));
    assert(!missing.available());
    assert(!missing.charging());
    assert(!missing.energy_remaining_wh());
    assert(!missing.energy_full_capacity_wh());
    assert(!missing.power_watts());

    const auto malformed = parse_power_supply_uevent(
        "POWER_SUPPLY_STATUS=Unknown\nPOWER_SUPPLY_POWER_NOW=not-a-number\n");
    assert(malformed.available());
    assert(!malformed.power_watts());
}
