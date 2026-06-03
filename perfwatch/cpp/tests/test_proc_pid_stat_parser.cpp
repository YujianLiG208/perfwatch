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

void test_proc_pid_stat_parser() {
    using perfwatch::platform_linux::parse_proc_pid_stat;

    const auto normal =
        parse_proc_pid_stat(read_linux_fixture("proc_pid_stat_normal.txt"));
    assert(normal);
    assert(normal->pid == 1234);
    assert(normal->comm == "perfwatchd");
    assert(normal->state == 'S');
    assert(normal->utime == 111);
    assert(normal->stime == 222);
    assert(normal->starttime == 333333);
    assert(normal->rss == 555);

    const auto with_spaces = parse_proc_pid_stat(
        read_linux_fixture("proc_pid_stat_name_with_spaces.txt"));
    assert(with_spaces);
    assert(with_spaces->pid == 4321);
    assert(with_spaces->comm == "my process name");
    assert(with_spaces->state == 'R');
    assert(with_spaces->utime == 987);
    assert(with_spaces->stime == 654);
    assert(with_spaces->starttime == 222222);
    assert(with_spaces->rss == 1024);

    assert(!parse_proc_pid_stat("1234 process-without-parentheses S 1 2 3"));
    assert(!parse_proc_pid_stat("1234 (too short) S 1 2 3"));
}
