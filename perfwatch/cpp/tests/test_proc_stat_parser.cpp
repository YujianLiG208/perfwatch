#include <cassert>
#include <cmath>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>

#include "perfwatch/linux/proc_parser.hpp"

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

void test_proc_stat_parser() {
    using perfwatch::platform_linux::ProcCpuTimes;
    using perfwatch::platform_linux::compute_cpu_usage_ratio;
    using perfwatch::platform_linux::parse_proc_stat_cpu;

    const auto normal =
        parse_proc_stat_cpu(read_linux_fixture("proc_stat_normal.txt"));
    assert(normal);
    assert(normal->user == 100);
    assert(normal->nice == 0);
    assert(normal->system == 50);
    assert(normal->idle == 1000);
    assert(normal->iowait == 0);
    assert(normal->irq == 0);
    assert(normal->softirq == 0);
    assert(normal->steal == 0);

    const auto missing =
        parse_proc_stat_cpu(read_linux_fixture("proc_stat_missing_fields.txt"));
    assert(missing);
    assert(missing->user == 150);
    assert(missing->nice == 5);
    assert(missing->system == 75);
    assert(missing->idle == 1200);
    assert(missing->iowait == 0);
    assert(missing->irq == 0);
    assert(missing->softirq == 0);
    assert(missing->steal == 0);

    ProcCpuTimes current = *normal;
    current.user += 50;
    current.system += 20;
    current.idle += 80;
    current.iowait += 10;
    const auto usage = compute_cpu_usage_ratio(*normal, current);
    assert(usage);
    assert(nearly_equal(*usage, 0.4375));

    assert(!compute_cpu_usage_ratio(current, *normal));
    assert(!parse_proc_stat_cpu("cpu not-a-number 0 0 0\n"));
}
