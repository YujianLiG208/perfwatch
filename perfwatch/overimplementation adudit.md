# 过度实施审计与实施记录

## 审计基线

- 审计日期：2026-09-14；替换记录更新：2026-09-15。
- 对齐时分支：`main`；当时本地 `HEAD` 与更新后的 `origin/main` 均为 `515a698be2dd7eed43e518aaa100528f0c2bede8`。
- 该提交为合并 Phase 9 的 PR #15。本地 `codex/phase9` 的提交为 `c8d1f7216039c4b98779cc1b4c857688e6e73c01`，是当前 `main` 的祖先。
- 两者文件树均为 `dc3a463dd4df19175294d2f2f16b580e4c72212e`，产品源代码完全一致。`main` 的提交记录还包含合并记录，不需要把它退回 Phase 9 的旧提交。
- 已撤销旧 Phase 7 基线上本轮替换的 8 个已跟踪文件改动，并删除新增的 `ui/dashboard/src/test/network.tsx`。没有保留这些替换的补丁或备份。
- 原有 `design and process audit.md`、发布产物及本地依赖/构建缓存不属于本轮替换源代码，未清理；它们不作为本次审计依据。依赖判断以已对齐的清单和锁文件为准。

参考：[GitHub 基线提交](https://github.com/YujianLiG208/perfwatch/commit/515a698be2dd7eed43e518aaa100528f0c2bede8)。

## 范围与判定

检查 C++ Windows 采集与 Python 绑定、Python 采集入口/分析/配置/API/存储/运行入口/悬浮窗、React Dashboard、构建打包脚本和 CI 配置。关注已有标准库、平台或成熟依赖能否承担通用实现；不以功能是否有用、文件是否长、是否存在少量重复文字作为结论。

以下保留版本对齐后的审计结论，位置引用对应上述审计基线。替换按用户指定顺序逐项进行，实施状态记录在文末；每项完成后停止。本记录不再统计阶段代码行数。

## 可替换项

### 1. 悬浮窗自行维护 Win32 接口绑定（新增，中优先级）

- 位置：`python/src/perfwatch/overlay/win32.py:55`、`:70`、`:255`。
- 重复实现：手工声明 `WNDCLASSW`、`PAINTSTRUCT`、回调签名、Win32 常量，以及函数参数和返回类型配置。这是通用 Windows Python 绑定工作。
- 实施：阶段 4 使用 `pywin32==312` 的 `win32gui`、`win32api`、`win32con`、`win32event` 替换手工结构体、回调签名、常量、DLL 加载和函数签名配置；消息循环直接使用 `PumpMessages()`。
- 边界：保留窗口布局、置顶/透明/点击穿透行为、绘制内容、HTTP 更新、父进程退出检测和资源清理。
- 接口适配：`BeginPaint` 返回设备上下文与绘制结构元组；矩形使用元组；字体使用 `LOGFONT`。主显示器工作区通过 `GetMonitorInfo(MonitorFromPoint((0, 0)))` 读取。父进程检测使用 `OpenProcess` 和 `WaitForSingleObject`，句柄通过 `Close()` 释放；保留打开父进程失败时继续 HTTP 更新的原行为。
- 异常边界：pywin32 自动抛出 Win32 调用错误。更新和关闭共用一个发送消息方法，仅忽略窗口已被 UI 线程销毁造成的无效窗口句柄错误，其余发送错误继续抛出。
- 成本：新增 Windows 条件依赖 `pywin32==312; sys_platform == 'win32'`，并在 Windows 分支中导入模块，保留非 Windows 环境导入数据模型及明确拒绝创建窗口的能力。未新增窗口封装类型或自定义打包钩子。
- 依据：[pywin32 GUI API](https://mhammond.github.io/pywin32/win32gui.html)、[项目与安装说明](https://github.com/mhammond/pywin32)。

### 2. HTTP 轮询与请求生命周期（原结论保留，高优先级）

- 位置：`ui/dashboard/src/useDashboardData.ts:73`、`:84`、`:137`、`:215`。
- 重复实现：轮询定时器、请求互斥、AbortController 生命周期、过期响应代次和请求加载状态，均由 Hook 手工维护。
- 替代：`@tanstack/react-query` 的 `useQuery`、`refetchInterval`、查询状态、同一 query key 的在途请求去重和 `queryClient.cancelQueries`；将库提供的 `signal` 传入现有 `fetch`。
- 边界：保留首次快照失败、历史/进程部分失败、60 点历史合并、WebSocket 优先和状态展示等业务规则。WebSocket 恢复时必须关闭轮询并取消在途 HTTP 请求，确保晚到的结果不会覆盖实时样本。不能只把 `enabled` 设为 false 就宣称取消完成。
- 实施：阶段 1 已采用 `@tanstack/react-query@5.102.8`。Hook 内创建独立 `QueryClient` 并直接传给 `useQuery`，复用原生 fetch，未新增 Provider 层。轮询、在途请求去重和取消交由库管理；展示状态及部分失败规则仍由应用维护。
- 依据：[轮询与在途请求去重](https://tanstack.com/query/latest/docs/framework/react/guides/polling)、[查询取消](https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation)。

### 3. WebSocket 重连状态机（原结论保留，中优先级）

- 位置：`ui/dashboard/src/useDashboardData.ts:149`、`:169`、`:280`，`ui/dashboard/src/connection.ts:1`。
- 重复实现：失败次数、退避定时器、连接重建、成功后的计数重置和卸载清理。
- 实施：阶段 2 采用 `partysocket@1.3.0` 的 `partysocket/ws` 通用客户端，继续连接当前 FastAPI WebSocket。删除应用内重连计数、计时器、连接重建和 `getReconnectDelay`，未新增封装层。
- 配置：最短重连间隔 1 秒、增长倍数 2、上限 10 秒，保留 1/2/4/8/10 秒退避。`minUptime: 0` 让库在连接打开后的计时任务中重置退避。显式采用库的 4 秒连接超时；相较旧实现，握手卡住也会触发降级和重连。
- 边界：URL 通过函数延迟解析，URL/原生 WebSocket 构造异常交由库捕获并触发错误处理。`onclose` 和 `onerror` 启动 HTTP 降级；`onopen` 停止轮询并取消在途查询。消息解析、历史合并和展示状态仍由应用负责。卸载时先清空应用事件回调，再调用 `close()` 终止重连。
- 成本：新增一个直接依赖 `partysocket` 及其传递依赖 `event-target-polyfill`。与 HTTP 替换共同修改现有 Hook，不引入 PartyKit 服务。
- 依据：[PartySocket 功能、通用 WebSocket 用法与选项](https://docs.partykit.io/reference/partysocket-api/)。

### 4. 进程文件名拆分与 UTF-8 转换（新增，低优先级）

- 位置：`cpp/platform/windows/windows_collector.cpp:52`。
- 重复实现：`find_last_of` / `substr` 提取文件名，再通过两次 `WideCharToMultiByte` 查询缓冲区大小并转换。
- 实施：阶段 5 使用 C++17 `std::filesystem::path` 从查询返回的宽字符范围构造路径，直接调用 `filename()` 和 `u8string()`，删除手工分隔符查找、子串提取和两次 `WideCharToMultiByte` 调用。
- 边界：保留 `QueryFullProcessImageNameW` 及现有缓冲区大小；查询失败、文件名为空或转换抛出 `std::system_error` 时返回 `unknown`。已核对当前 MSVC 标准库的转换错误类型，不仅捕获其派生类 `filesystem_error`。保留返回类型 `std::string` 及现有调用接口。
- 成本：仅新增标准库头文件，无第三方依赖、生产接口或新封装类型。
- 依据：[Microsoft C++ path::filename 与 path::u8string](https://learn.microsoft.com/en-us/cpp/standard-library/path-class?view=msvc-170)。

### 5. 环境变量布尔词表（原结论保留，低优先级）

- 位置：`python/src/perfwatch/config/settings.py:27`。
- 重复实现：手写 `1/0`、`true/false`、`yes/no`、`on/off` 两组词表。
- 实施：阶段 3 已使用标准库 `ConfigParser.BOOLEAN_STATES` 替换手写词表，与原有八个值一致。
- 边界：继续保留环境变量读取、缺失默认值、去空白、忽略大小写和原有 ValueError 提示。
- 成本：仅增加标准库导入，直接复用映射；未增加配置框架、封装层或第三方依赖。
- 依据：[ConfigParser.BOOLEAN_STATES](https://docs.python.org/3/library/configparser.html#configparser.ConfigParser.BOOLEAN_STATES)。

## 暂缓与排除

- **信息解析和采集接口的大规模替换继续暂缓。** 不批量重写快照字段转换、数据库映射、Python/C++ 接口，也不将整个 Windows 采集器迁移到其他采集库。这些改动需要单独核对字段、单位、缺失值和历史兼容语义，不能视为直接替换。
- **旧 Linux 解析器结论不再适用于当前基线。** 当前版本已删除 Linux 解析器及其样本，不再记录为待替换实现。
- `ProcessorPowerInformation` 的手工声明不列为重复实现：微软文档明确说明该结构曾从 WinNT.h 遗漏，并要求应用自行提供定义。不能仅根据文档中存在类型名就假定 SDK 已可直接导入。[微软说明](https://learn.microsoft.com/en-us/windows/win32/power/processor-power-information-str)
- SQLite 已直接使用 `sqlite3`、事务、`executemany`、SQL 排序及 LIMIT；FastAPI 已承担路由、查询参数约束、静态文件和 WebSocket 传输；图表已用 Recharts，日期已用 Intl。没有足够理由再引入 ORM、调度器或另一套 UI 框架。
- 简短的能耗公式、Unavailable 展示、Top 10 选择、启动就绪检查是产品规则或对平台 API 的组合，不单凭“有类似第三方包”判为必须替换。
- 构建脚本和 PyInstaller 配置中的 `build/phase8` 是沿用的构建目录名，不是 Git 分支。本轮始终在 `main` 工作，没有进入或修改 `codex/phase8`。

## 验证与执行状态

- 版本对齐时已确认 `HEAD == origin/main`，且与 `codex/phase9` 文件树相同、包含 Phase 9 提交。后续五项替换在 `main` 实施；用户现已授权提交并推送，两份审计文档一并纳入版本管理。交付版本及远端同步状态以 Git 提交记录为准。
- 按用户指定的实施顺序记录如下（与上文审计排序区分）：

| 阶段 | 替换 | 状态 |
| --- | --- | --- |
| 1 | HTTP 轮询 → TanStack Query | 用户确认完成；按要求不追加该阶段的最终验证 |
| 2 | WebSocket 重连 → partysocket | 已完成，用户已授权进入阶段 3 |
| 3 | 布尔词表 → ConfigParser | 已完成，用户已授权进入阶段 4 |
| 4 | 悬浮窗接口声明 → pywin32 | 已完成，用户已授权进入阶段 5 |
| 5 | 进程名拆分和编码转换 → C++17 std::filesystem | 已完成，在本阶段门禁停止 |

- 阶段 2 验证：现有 `useDashboardData.test.tsx`、`App.test.tsx`、`connection.test.ts` 中共 14 个测试通过；未新增测试文件。测试使用原生 WebSocket 的事件替身，实际执行 partysocket 的重连逻辑，检查退避及打开后重置、构造失败、握手超时、HTTP 降级取消、旧连接消息隔离和卸载停止。
- 阶段 2 的 TypeScript 检查和 Vite 生产构建通过。构建提示压缩后主包超过 500 kB，并提示解析插件耗时；未为此扩展本阶段范围。
- 阶段 2 未开展真实浏览器与 FastAPI 服务端的端到端运行检查，测试结果不代表该项验证已完成。
- 阶段 3 验证：仅运行现有 `python/tests/test_settings.py`，2 个测试通过。在该文件补充一个聚焦检查，覆盖环境变量缺失时的默认值、去空白、忽略大小写、真假值以及原有非法值错误提示；未新增测试文件，也未重复运行其他阶段的测试。
- 阶段 4 验证：现有 `python/tests/test_overlay.py` 的 2 个测试通过；只扩充其中的真实窗口检查，验证绘制更新、窗口尺寸、透明度、置顶、点击穿透和关闭后的窗口/字体清理。修改文件的 Ruff 检查通过，未新增测试文件。
- 阶段 4 打包验证：使用现有 `packaging/perfwatch.spec` 和 PyInstaller 6.22.2 构建检查用包，确认自动包含 `win32api.pyd`、`win32gui.pyd`、`win32event.pyd` 和 `pywintypes312.dll`。生成的程序成功创建悬浮窗，在检查用父进程退出后正常关闭，退出码为 0、标准错误为空。未修改打包配置或增加 hidden imports。
- 该检查用包复用了现有前端和原生采集器构建产物，只验证本阶段的悬浮窗依赖与生命周期，不作为完整发布构建。打包提示可选的 `tzdata` 未找到；未为此扩展本阶段范围。阶段 4 门禁时未重复执行其他阶段测试，未提交、推送或发布。
- 阶段 5 验证：MSVC C++17 Debug 构建通过，现有 CTest 目标 `perfwatch_cpp_tests` 通过，断言保持启用。构建目录中的一次性检查程序直接调用生产代码的内部函数，确认真实进程 `监测🚀.exe` 的名称返回正确 UTF-8 字节，并确认无效进程句柄返回 `unknown`；未新增仓库测试套件或测试专用生产接口。
- 阶段 5 只重建 C++ 核心和现有 C++ 测试，未重建 Python 原生扩展或发布包，未重复运行前四阶段测试。五项替换均已完成，信息解析接口的大规模替换继续暂缓。本次提交同步源码、依赖清单及审计记录；本地依赖、数据库、构建缓存及发布产物仍按现有 Git 忽略规则保留。

## 过度测试审查与调整（2026-09-19）

本轮基于 `main` 的 `b1245499bdb7c21b85cb96c5d571612c414af23e`（PR #16 合并提交）重新审查。
范围为测试用例的重复覆盖、实施与 CI 的执行成本，以及测试缓存和临时产物。
按用户要求先完成用例删除与合并并停止，再调整测试方法和 CI 范围。

### 已删除和合并的测试

| 调整 | 保留的有效覆盖 |
| --- | --- |
| 删除独立 `/health` 测试 | Dashboard 挂载集成测试继续检查状态码及健康响应 |
| 删除显式命令行参数解析测试 | 服务入口测试继续检查 host、port 和 Dashboard 目录实际生效 |
| 删除能耗评分的重复计算一致性测试 | enrichment 测试继续核对同一输入的准确评分 `0.1` |
| 合并服务启动和停止测试 | 同一服务实例检查快照生成、任务运行及停止后的任务状态 |
| 合并两项 Unavailable 显示测试 | 保留缺失测量值、进程评分单元格及能耗卡片的明确断言 |

SQLite 迁移与回滚、输入边界、陈旧响应隔离、卸载清理、真实 Win32 窗口及发布包 smoke
具有独立验证价值，继续保留。未建立新的测试矩阵或测试框架。

### 已调整的测试方法与 CI 范围

- 新增标准库脚本 `scripts/ci_scope.py`，比较 PR 基线或 push 前一提交与当前检出内容；
  按原路径处理删除与重命名，首个 push 的空基线按空树处理。
- Markdown 文档变更跳过产品检查；前端变更只选择前端测试与构建；Python 变更选择后端测试和
  Ruff；C++ 变更选择后端与原生构建检查。Python 依赖配置变更同时选择原生检查。
  工作流、脚本或打包配置变更选择全部检查，pre-commit 配置变更选择 Ruff。
- 保留 Windows/Ubuntu 与 Python 3.11/3.12 的现有四格矩阵；普通 Python 修改不安装 pybind11、
  不重新编译 C++。需要原生检查时，一次构建同时要求测试目标和 Python 原生扩展目标存在。
- 保留 `python-cpp`、`frontend`、`quality` 必需检查名称。仅在任务层跳过无关检查，工作流仍运行；
  后端汇总要求变更检测成功，且矩阵成功或被明确跳过，检测失败不能作为成功放行。
- Ruff 任务只安装 Ruff，检查 Python 源码、测试及脚本；后端测试任务安装产品依赖和 pytest，
  不再额外安装 Ruff。
- C++ 测试文件在包含 `<cassert>` 前取消 `NDEBUG`，让 Release 构建也执行断言；
  不改变发布程序的优化配置。
- 打包 smoke 为子进程设置独立的临时 `LOCALAPPDATA`，在子进程结束后自动清理，
  失败退出同样清理，避免 mock 样本写入用户数据库。
- 文档明确：实施期间使用受影响的聚焦检查及相关最终门禁；仅在打包、原生依赖、运行入口
  相关改动或发布准备时重新验证完整包。无相关变化、失败或新证据时不重复执行检查。
- 对新增路径选择逻辑和 smoke 数据隔离各保留一个聚焦回归检查，没有新增第三方依赖。

### 验证结果与交付边界

- 用例精简阶段：受影响的 Python 测试及现有能耗结果检查共 16 项通过；`App.test.tsx` 的
  6 项测试通过；差异格式检查通过。
- 方法调整阶段：CI 范围选择和 smoke 隔离/失败清理检查各 1 项通过；修改脚本与新增测试的
  Ruff 检查通过。提交前，按新 CI 范围检查 Python 源码、测试及脚本的 Ruff 门禁和差异格式检查均通过。
- C++ Release 验证：沙箱内 MSBuild FileTracker 遇到访问权限问题后停止。
  用户已在本机手动完成 C++ 构建和 CTest，并反馈通过；此项为用户确认结果，未由代理重复执行。
- 本轮没有重新运行完整测试套件、重建完整发布包或验证真实 GitHub Actions 执行结果。
  远端 CI 状态以推送后的 GitHub Actions 结果为准。
- 缓存和临时文件仅提供清理候选，用户选择自行在 File Explorer 中清理；代理未执行历史产物清理。
  依赖环境、正式 ZIP/校验文件和真实运行数据库不作为可直接删除的测试垃圾。
- 用户已授权将本轮代码、CI 配置和审查文档一并提交并推送；提交及远端同步状态以 Git 记录为准。
