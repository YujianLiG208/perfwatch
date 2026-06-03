#include <cassert>
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

}  // namespace

void test_meminfo_parser() {
    using perfwatch::platform_linux::parse_proc_meminfo;

    const auto normal =
        parse_proc_meminfo(read_linux_fixture("proc_meminfo_normal.txt"));
    assert(normal.total_bytes);
    assert(*normal.total_bytes == 33554432ULL * 1024ULL);
    assert(normal.mem_available_bytes);
    assert(*normal.mem_available_bytes == 16777216ULL * 1024ULL);
    assert(normal.mem_free_bytes);
    assert(*normal.mem_free_bytes == 8388608ULL * 1024ULL);
    assert(normal.buffers_bytes);
    assert(*normal.buffers_bytes == 524288ULL * 1024ULL);
    assert(normal.cached_bytes);
    assert(*normal.cached_bytes == 4194304ULL * 1024ULL);
    assert(normal.swap_total_bytes);
    assert(*normal.swap_total_bytes == 2097152ULL * 1024ULL);
    assert(normal.swap_free_bytes);
    assert(*normal.swap_free_bytes == 1048576ULL * 1024ULL);
    assert(normal.used_bytes());
    assert(*normal.used_bytes() == 16777216ULL * 1024ULL);

    const auto minimal =
        parse_proc_meminfo(read_linux_fixture("proc_meminfo_minimal.txt"));
    assert(minimal.total_bytes);
    assert(!minimal.mem_available_bytes);
    assert(minimal.available_bytes());
    assert(*minimal.available_bytes() == 400ULL * 1024ULL);
    assert(minimal.used_bytes());
    assert(*minimal.used_bytes() == 600ULL * 1024ULL);
    assert(!minimal.swap_total_bytes);
    assert(!minimal.swap_free_bytes);

    const auto malformed = parse_proc_meminfo("MemTotal: nope kB\n");
    assert(!malformed.total_bytes);
    assert(!malformed.used_bytes());
}
