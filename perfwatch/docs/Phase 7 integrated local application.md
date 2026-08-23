# Phase 7 Integrated Local Application

**Status:** In progress — Phase 7A validated

**Date:** 2026-08-23

**Branch:** `codex/phase7`

**Worktree:** Codex linked worktree `4e73`

## Purpose

Record the implementation and validation evidence for Roadmap Phase 7. This note is updated after
each functional work item. The current record covers Phase 7A only: deterministic evolving mock
samples across the pure Python, native-compatible Python, C++, and pybind paths.

## Phase 7A — Deterministic Evolving Mock Samples

### Delivered Behavior

- Python and C++ mock factories accept an optional non-negative `sample_index`.
- Index zero preserves the existing Phase 1 baseline snapshot.
- Timestamps advance by 1,000 milliseconds per index from `1710000000000`.
- CPU, memory, battery, and process fields follow the approved bounded triangular formulas.
- GPU fields remain at the existing unavailable baseline.
- Python `MockCollector`, Python `NativeCollector`, and C++ `MockCollector` each own an independent
  counter and increment it after a successful sample.
- Python `get_snapshot()` and the pybind `get_mock_snapshot()` retain index-zero defaults for
  backward-compatible one-shot calls.
- The native-compatible wrapper passes its index to the compiled extension when present and to the
  pure Python factory otherwise.

### Changed Interfaces and Files

| File | Interface or behavior change |
| --- | --- |
| `python/src/perfwatch/collectors/mock.py` | Added `_triangle()`, `get_mock_snapshot(sample_index=0)`, negative-index validation, deterministic formulas, and stateful `MockCollector`. |
| `python/src/perfwatch/collectors/native.py` | Added `get_snapshot(sample_index=0)` and stateful `NativeCollector`; both native and fallback paths receive the index. |
| `python/tests/test_mock_collector.py` | Added baseline, explicit-index, repeatability, independent-state, battery-boundary, invalid-index, native-boundary, and fallback tests. |
| `cpp/include/perfwatch/collector.hpp` | Added the indexed factory declaration and `MockCollector::sample_index_`. |
| `cpp/src/collector.cpp` | Added the integer triangle helper, approved formulas, and successful-collection index advancement. |
| `cpp/bindings/pybind_module.cpp` | Added optional `sample_index` to `get_mock_snapshot` and delegated directly to the indexed factory. |
| `cpp/tests/test_mock_collector.cpp` | Replaced fixed-snapshot equality checks with baseline, indexed, repeatability, cycle-boundary, and independent-state assertions. |

No new dependency, source file, runtime abstraction, hardware collector behavior, endpoint, or
packaging behavior was added.

### Test-Driven Implementation Evidence

| Step | Command or observation | Result |
| --- | --- | --- |
| Python baseline | `python -m pytest python/tests/test_mock_collector.py -q` before new tests | `1 passed` |
| Python mock RED | Same command after indexed tests were added | `8 failed`; the factory rejected the new positional index and collectors returned a fixed timestamp. |
| Python mock GREEN | Same command after the indexed factory and collector were implemented | `8 passed` |
| Native wrapper RED | Same command after native/fallback tests were added | `8 passed, 3 failed`; `get_snapshot()` rejected an index and both native-compatible paths reset state. |
| Native wrapper GREEN | Same command after indexed forwarding and state were implemented | `11 passed` |
| C++ RED | `cmake --build build-phase7` after indexed C++ assertions were added | Compilation failed with MSVC `C2660`: `make_mock_snapshot` did not take one argument. |
| C++ GREEN build | `cmake --build build-phase7` after the factory, collector, and binding were implemented | Core library, test executable, and `perfwatch_native.cp312-win_amd64.pyd` built successfully. |
| C++ targeted GREEN | `ctest --test-dir build-phase7 --output-on-failure -R perfwatch_cpp_tests` | `1/1` passed. |
| Real pybind smoke | Imported the extension directly from `build-phase7` and called indices 0 and 3 | Printed `1710000000000 1710000003000 47.0`; all assertions passed. |

The RED failures matched the missing behavior rather than syntax, test-discovery, or dependency
errors. Production changes were made only after the corresponding failure was observed.

### Stage 3 Validation Evidence

| Validation | Result |
| --- | --- |
| `python -m pytest python/tests/test_mock_collector.py -q` | PASS — `11 passed in 0.04s` |
| `python -m ruff check python/src/perfwatch/collectors python/tests/test_mock_collector.py` | PASS — `All checks passed!` |
| Explicit MSVC/Ninja/Python/pybind11 CMake configure | PASS — `Configuring done` and `Generating done` |
| `cmake --build build-phase7` | PASS — `ninja: no work to do.` |
| `ctest --test-dir build-phase7 --output-on-failure` | PASS — `1/1` passed, 0 failed |

Stage 3 intentionally ran the Phase 7A scoped Python and C++ validation rather than the complete
repository acceptance suite. Full Python, frontend, and native acceptance remains scheduled for
Phase 7D.

### Toolchain Paths and Environment Recovery

The validated native toolchain used these exact paths:

| Tool | Validated path |
| --- | --- |
| Ninja | `C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe` |
| MSVC compiler | `C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.51.36231\bin\HostX64\x64\cl.exe` |
| Python | `C:\Users\Yujian Li\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` |
| pybind11 CMake directory | `C:\Users\Yujian Li\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages\pybind11\share\cmake\pybind11` |
| Visual Studio environment script | `C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\Launch-VsDevShell.ps1` |

Two environment issues were corrected before validation:

1. The shared Python runtime's editable `perfwatch` installation pointed to an older `9bd6`
   worktree. It was reinstalled with `--no-deps -e .\python` from `4e73`, after which the imported
   module path and indexed signature matched the active worktree.
2. MSVC environment variables were not inherited by new PowerShell processes, and the first CMake
   attempt cached `CMAKE_CXX_COMPILER-NOTFOUND`. Native commands now load `Launch-VsDevShell.ps1`
   in the same process. The failed generated directory was preserved during diagnosis as
   `build-phase7-failed-compiler-cache`, and a fresh `build-phase7` configuration identified MSVC
   19.51.36246, Ninja, Python, and pybind11.

The final configure/build/CTest group passed without a Ninja error. The project owner therefore
confirmed that the earlier Ninja path issue is resolved and no additional Ninja-only stop is
required during later Phase 7 work.

### Remaining Limitations

- Mock samples are deterministic fixtures, not live Windows sensor readings.
- GPU data intentionally remains unavailable.
- The process score in a raw Phase 7A mock is still the deterministic fixture value; shared
  analytics recomputation is Phase 7B scope.
- Phase 7A does not add battery runtime estimation, SQLite migration, dashboard presentation, or
  the integrated production server; those remain Phase 7B and Phase 7C work.
- Packaging, installers, services, and release distribution remain Phase 8 work.

### Commit Scope Adjustment

The first Stage 5 review found that the approved detailed plan and two generated build directories
would prevent the Stage 6 clean-worktree check from succeeding. The project owner authorized a
local return to Stage 4 with these decisions:

- include `docs/superpowers/plans/2026-08-23-phase-7-integrated-local-application.md` in the Phase
  7A documentation commit scope;
- delete `build-phase7` and `build-phase7-failed-compiler-cache` after their validation evidence
  had been recorded because both directories are reproducible generated output; and
- replace a repeated full Stage 5 review with a limited status check proving the detailed plan is
  present and both generated directories are absent.

## Next Pipeline Stage

After the limited status check, Phase 7A proceeds to Stage 6. The commit must contain exactly the
seven implementation files, this process note, and the approved detailed implementation plan; it
must not contain generated build output.
