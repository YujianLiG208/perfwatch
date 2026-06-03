cmake_minimum_required(VERSION 3.20)

project(perfwatch LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(perfwatch_core
    src/snapshot.cpp
    src/collector.cpp
    src/platform_common.cpp
    platform/linux/linux_collector.cpp
    platform/linux/proc_parser.cpp
    platform/linux/power_supply_parser.cpp
    platform/windows/windows_collector.cpp
    platform/windows/pdh_collector.cpp
    platform/windows/wmi_fallback.cpp
    gpu/gpu_fallback.cpp
)

target_include_directories(perfwatch_core
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
        ${CMAKE_CURRENT_SOURCE_DIR}/gpu
)

target_compile_features(perfwatch_core PUBLIC cxx_std_17)

enable_testing()

add_executable(perfwatch_cpp_tests
    tests/test_snapshot.cpp
    tests/test_mock_collector.cpp
)
target_link_libraries(perfwatch_cpp_tests PRIVATE perfwatch_core)
add_test(NAME perfwatch_cpp_tests COMMAND perfwatch_cpp_tests)

find_package(Python3 COMPONENTS Interpreter Development.Module QUIET)
if(Python3_Interpreter_FOUND)
    execute_process(
        COMMAND "${Python3_EXECUTABLE}" -m pybind11 --cmakedir
        OUTPUT_VARIABLE PERFWATCH_PYBIND11_CMAKE_DIR
        ERROR_QUIET
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    if(PERFWATCH_PYBIND11_CMAKE_DIR)
        list(APPEND CMAKE_PREFIX_PATH "${PERFWATCH_PYBIND11_CMAKE_DIR}")
    endif()
endif()

find_package(pybind11 CONFIG QUIET)
if(pybind11_FOUND)
    pybind11_add_module(perfwatch_native bindings/pybind_module.cpp)
    target_link_libraries(perfwatch_native PRIVATE perfwatch_core)
else()
    message(STATUS "pybind11 not found; skipping perfwatch_native module build for Phase 1 skeleton.")
endif()
