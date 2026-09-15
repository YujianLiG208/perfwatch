# Design and Process Audit / 设计与过程审查

## Audit record / 审查记录

| Item | 中文 | English |
| --- | --- | --- |
| Date | 2026-09-01 | 2026-09-01 |
| Target | `codex/phase9`，删减前提交 `42982ae` | `codex/phase9`, pre-audit commit `42982ae` |
| Scope | 代码设计、测试过程、发布校验、长期文档 | Code design, testing process, release checks, and durable documentation |
| Delivery at audit time | 历史记录：2026-09-01 审查时，本文件及当时改动尚未提交、未推送 | Historical record: this file and the changes were uncommitted and unpushed at the 2026-09-01 audit |

## Design reductions / 设计删减

| 中文 | English |
| --- | --- |
| 删除没有产品调用方、仅为未来计划保留的 Linux parser/collector、GPU 接口、平台探测及 fixtures。 | Removed Linux parsers/collector, GPU interfaces, platform probes, and fixtures that had no product callers and existed only for future plans. |
| 删除 C++ mock collector 与 `Collector` 单实现继承层；C++ 仅保留真实 `WindowsCollector`，显式 mock 由 Python 提供。 | Removed the C++ mock collector and single-implementation `Collector` hierarchy; C++ now keeps only the real `WindowsCollector`, while Python owns the explicit mock. |
| 将 `SnapshotRepository` 合并进 `SQLiteWriter`，只保留应用真实使用的初始化、单快照写入、事件写入、历史指标和 top-process 查询。 | Folded `SnapshotRepository` into `SQLiteWriter`, retaining only initialization, single-snapshot writes, event writes, recent metrics, and top-process queries used by the application. |
| 删除旧 `perfwatch.cli`、一次性 native `get_snapshot()`、空 `close()`、批量/独立 process/通用时间窗/retention API。 | Removed the legacy `perfwatch.cli`, one-shot native `get_snapshot()`, no-op `close()`, and unused batch/process/window/retention APIs. |
| 从运行时依赖移除 `pytest`，从开发依赖移除未使用的 `mypy`。 | Removed `pytest` from runtime dependencies and unused `mypy` from development dependencies. |
| 发布 ZIP 校验只保留一次解压布局检查，删除压缩前后的重复布局、hash 和 checksum 自证。 | Reduced ZIP verification to one extraction/layout check and removed duplicate pre/post layout, hash, and checksum self-checks. |

## Test and process reductions / 测试与过程删减

| 中文 | English |
| --- | --- |
| 删除只保护已移除 Linux/C++ mock 代码的测试和 fixtures。 | Removed tests and fixtures that only protected deleted Linux/C++ mock code. |
| SQLite 测试由 14 项收缩为四个风险场景：迁移、真实读写、事务回滚、事件。 | Reduced SQLite coverage from 14 tests to four risk scenarios: migration, real read/write, transaction rollback, and events. |
| Python mock 测试保留 baseline/evolution、实例状态、输入边界和 native 选择策略。 | Kept focused Python mock coverage for baseline/evolution, instance state, input validation, and native selection policy. |
| Dashboard Hook 测试删除完整退避矩阵和等价清理分支，保留初始/live、断线 fallback、陈旧响应、卸载清理和致命错误。 | Removed the complete backoff matrix and equivalent cleanup branches from the Dashboard Hook tests; retained initial/live, disconnect fallback, stale response, unmount cleanup, and fatal error scenarios. |
| Phase 9 的 38 项逐条手工记录压缩为耐久验收事实。 | Condensed the 38-item Phase 9 manual transcript into durable acceptance facts. |

## Documentation reductions / 文档删减

| 中文 | English |
| --- | --- |
| 删除 `docs/superpowers` 下 9 份历史 plan/spec（6,084 行）。 | Removed nine historical plan/spec files under `docs/superpowers` (6,084 lines). |
| 删除 Phase 3-5、7、8 的命令级过程记录及 superseded CI/CD 设计。 | Removed command-level Phase 3-5, 7, and 8 process notes and the superseded CI/CD design. |
| Phase 9 文档只保留环境类别、已验证行为、release evidence 和签名限制。 | Reduced the Phase 9 document to environment class, accepted behavior, release evidence, and signing limitation. |
| 将 README、Scope、Roadmap、Architecture、Testing Strategy、Dashboard README 和 AGENTS 同步为当前 Windows 产品的短版事实来源。 | Synchronized README, Scope, Roadmap, Architecture, Testing Strategy, Dashboard README, and AGENTS as concise sources of truth for the current Windows product. |
| 删除已经与真实实现冲突的 Overlay placeholder。 | Removed the Overlay placeholder that contradicted the implemented product. |

## Validation / 验证

| Check | Result / 结果 |
| --- | --- |
| `python -m pytest python/tests -q` | PASS — 47 passed; one upstream Starlette/httpx deprecation warning |
| `python -m ruff check python/src python/tests` | PASS |
| `npm.cmd test` | PASS — 23 passed across 4 files |
| `npm.cmd run build` | PASS — existing Recharts chunk-size advisory remains |
| `cmake -S cpp -B build` | PASS; optional pybind11 was not present in this environment |
| `cmake --build build --config Debug` | PASS after approved execution outside the sandbox because MSBuild FileTracker was denied inside it |
| `ctest --test-dir build --output-on-failure -C Debug` | PASS — 1/1 |
| `git diff --check` | PASS; only Git LF-to-CRLF notices |

The optional native Python module and full Windows release package were not rebuilt because pybind11
was not available in the default validation environment. No dependency was installed and no release
artifact was changed.

默认验证环境没有 pybind11，因此未重新构建可选 native Python 模块和完整 Windows 发布包。本次未安装
依赖，也未更改发布产物。

## Change size / 变更规模

Excluding this local audit file, tracked changes contain 222 added lines and 9,888 deleted lines
across 79 files: net **−9,666 lines**.

不含本地审查文件，跟踪改动覆盖 79 个文件：新增 222 行、删除 9,888 行，净减少 **9,666 行**。
