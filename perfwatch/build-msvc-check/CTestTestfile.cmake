# CMake generated Testfile for 
# Source directory: C:/Users/Yujian Li/.codex/worktrees/9bd6/Performance & Energy Monitor/perfwatch/cpp
# Build directory: C:/Users/Yujian Li/.codex/worktrees/9bd6/Performance & Energy Monitor/perfwatch/build-msvc-check
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
if(CTEST_CONFIGURATION_TYPE MATCHES "^([Dd][Ee][Bb][Uu][Gg])$")
  add_test([=[perfwatch_cpp_tests]=] "C:/Users/Yujian Li/.codex/worktrees/9bd6/Performance & Energy Monitor/perfwatch/build-msvc-check/Debug/perfwatch_cpp_tests.exe")
  set_tests_properties([=[perfwatch_cpp_tests]=] PROPERTIES  _BACKTRACE_TRIPLES "C:/Users/Yujian Li/.codex/worktrees/9bd6/Performance & Energy Monitor/perfwatch/cpp/CMakeLists.txt;45;add_test;C:/Users/Yujian Li/.codex/worktrees/9bd6/Performance & Energy Monitor/perfwatch/cpp/CMakeLists.txt;0;")
elseif(CTEST_CONFIGURATION_TYPE MATCHES "^([Rr][Ee][Ll][Ee][Aa][Ss][Ee])$")
  add_test([=[perfwatch_cpp_tests]=] "C:/Users/Yujian Li/.codex/worktrees/9bd6/Performance & Energy Monitor/perfwatch/build-msvc-check/Release/perfwatch_cpp_tests.exe")
  set_tests_properties([=[perfwatch_cpp_tests]=] PROPERTIES  _BACKTRACE_TRIPLES "C:/Users/Yujian Li/.codex/worktrees/9bd6/Performance & Energy Monitor/perfwatch/cpp/CMakeLists.txt;45;add_test;C:/Users/Yujian Li/.codex/worktrees/9bd6/Performance & Energy Monitor/perfwatch/cpp/CMakeLists.txt;0;")
elseif(CTEST_CONFIGURATION_TYPE MATCHES "^([Mm][Ii][Nn][Ss][Ii][Zz][Ee][Rr][Ee][Ll])$")
  add_test([=[perfwatch_cpp_tests]=] "C:/Users/Yujian Li/.codex/worktrees/9bd6/Performance & Energy Monitor/perfwatch/build-msvc-check/MinSizeRel/perfwatch_cpp_tests.exe")
  set_tests_properties([=[perfwatch_cpp_tests]=] PROPERTIES  _BACKTRACE_TRIPLES "C:/Users/Yujian Li/.codex/worktrees/9bd6/Performance & Energy Monitor/perfwatch/cpp/CMakeLists.txt;45;add_test;C:/Users/Yujian Li/.codex/worktrees/9bd6/Performance & Energy Monitor/perfwatch/cpp/CMakeLists.txt;0;")
elseif(CTEST_CONFIGURATION_TYPE MATCHES "^([Rr][Ee][Ll][Ww][Ii][Tt][Hh][Dd][Ee][Bb][Ii][Nn][Ff][Oo])$")
  add_test([=[perfwatch_cpp_tests]=] "C:/Users/Yujian Li/.codex/worktrees/9bd6/Performance & Energy Monitor/perfwatch/build-msvc-check/RelWithDebInfo/perfwatch_cpp_tests.exe")
  set_tests_properties([=[perfwatch_cpp_tests]=] PROPERTIES  _BACKTRACE_TRIPLES "C:/Users/Yujian Li/.codex/worktrees/9bd6/Performance & Energy Monitor/perfwatch/cpp/CMakeLists.txt;45;add_test;C:/Users/Yujian Li/.codex/worktrees/9bd6/Performance & Energy Monitor/perfwatch/cpp/CMakeLists.txt;0;")
else()
  add_test([=[perfwatch_cpp_tests]=] NOT_AVAILABLE)
endif()
