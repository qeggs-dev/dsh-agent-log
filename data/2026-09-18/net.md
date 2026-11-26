<!-- 20260918-024 -->

## VES 的 net 环境位于 `D

\Projects\Deepseek_Harness_Workspace\envs\net\.venv`，其解释器是 `envs\net\.venv\Scripts\python.exe`（Python 3.14.3），由 `ves.bat create net` 创建；

用 `ves.bat list` 可查看当前存在的环境

<!-- 20260918-025 -->

## net 环境已装依赖（实测版本）

pydantic 2.13.5、orjson 3.12.0、httpx 0.28.1、requests 2.34.2、aiohttp 3.14.3、websockets 17.1、numpy 2.5.3、pandas 3.0.6；完整冻结清单在工作区 `net-requirements.txt`（29 行）

<!-- 20260918-026 -->

## 工作区操作手台由 `console.bat`（纯 ASCII 启…

工作区操作手台由 `console.bat`（纯 ASCII 启动器，会设 PYTHONUTF8=1）与 `net_console.py` 组成，用**工作区根 `.venv`**（Python 3.11.9）解释器运行（2026-09-18 修订：原为 VES 的 net 环境，改动理由见 20260918-041）；

子命令为 libs、selftest、req、probe、validate、fmt、bench，结果一律以 JSON 写到 stdout；退出码约定 0 成功 / 1 网络错误 / 2 校验失败 / 3 用法或输入错误

<!-- 20260918-027 -->

## 操作手台各子命令职责

req 输出状态码、耗时、选定响应头与 JSON 正文（超 `--max-chars` 自动截断）并用内置 Envelope 模型自校验；probe 分段测量 DNS/TCP/TLS/首字节耗时并返回 TLS 版本与证书到期时间；

validate 用 pydantic 校验（内置 item、envelope、probe，或 `<file.py>:<ClassName>`）；bench 对比 orjson 与标准库；fmt 格式化或压缩 JSON

<!-- 20260918-028 -->

## 实测性能（net 环境，3000 条记录）

orjson 比标准库 json 的 dumps 快 9.38 倍、loads 快 2.51 倍，序列化体积小 12%；pydantic 校验吞吐约 34 万条/秒

<!-- 20260918-029 -->

## 关键约束

workspace-write 沙箱下建环境与装包**必失败**——`tempfile.mkdtemp()` 建的目录（0o700）会被拒绝访问，导致 ensurepip 报 PermissionError、pip 无输出卡死（改 TEMP/TMP 到工作区也无效）；

`ves.bat create`/`install` 必须在 danger-full-access 下执行，实测该模式下 create net 约 20 秒、exit 0

<!-- 20260918-030 -->

## 操作手台使用陷阱

`console.bat` 必须保持**纯 ASCII**（cmd 按 OEM 代码页解析 .bat，中文注释会打乱语句结构）且 `rem` 注释里不能出现 `<`/`>`（会被当成重定向，报 cannot find the path）；

经 cmd 传内联 JSON 时 `--data` 的双引号会被 cmd 吃掉，改用 stdin 管道传入；脚本读 stdin 走字节层，以避开 locale（GBK）解码把中文变成孤立代理项

<!-- 20260918-031 -->

## `ves.bat shell net` 在无 TTY 环境下也可执行

内部跑 `powershell -NoLogo -NoExit -File activate.ps1`，stdin 管道立即 EOF，约 1.6 秒后正常退出（exit 0），提示符出现 `(net)` 前缀证明激活已生效；但该会话无法交互使用

<!-- 20260918-032 -->

## 0o700 权限的目录（包括 `tempfile.mkdtemp…

0o700 权限的目录（包括 `tempfile.mkdtemp()` 的全部产物）在 workspace-write 下除了不可写、不可列，还**不可删除**——`Remove-Item -Recurse -Force` 与 `icacls /reset` 均报 Access denied，故这类目录一旦生成就会永久残留，只能从沙箱外清理；

工作区 `D:\Projects\Deepseek_Harness_Workspace\.tmp\` 下现存 11 个此类空目录（c_mode700、mode700、fresh_*、tmp* 等）是沙箱诊断遗留，不是故障

<!-- 20260918-039 -->

## 工作区根新增 `to_venv.bat`

转发到根 `.venv` 里任意工具，用法是先 `set "L=pip.exe"` 再 `to_venv.bat --version`，`L` 默认 `python.exe`，内部路径用 `%~dp0.venv\Scripts\%L%` 故任意 cwd 都可用；

批处理里变量**必须**写 `%L%`——单 `%L` 只在 cmd 交互行有效，写成单百分号时 cmd 会把 `%L" %` 整体当成变量名吃掉，报 `'".\.venv\scripts\*' is not recognized`，此坑已修

<!-- 20260918-040 -->

## 工作区根 `.venv` 是 Python 3.11.9，装有…

工作区根 `.venv` 是 Python 3.11.9，装有 orjson 3.12.0 / httpx 0.28.1 / pydantic 2.13.5 / requests 2.34.2 / numpy 2.4.6 / pandas 3.0.6；

**缺 aiohttp 与 websockets**（手台只 import orjson/httpx/pydantic，故 `console.bat libs` 里这两项显示 null 属正常、不是故障）；

`net-requirements.txt` **不能原样装到 3.11**——其中 `numpy==2.5.3` 的 requires_python 是 `>=3.12`，这正是 `.venv` 里 numpy 退到 2.4.6 的原因；

aiohttp 3.14.3 与 websockets 17.1 在 cp311 win_amd64 都有 wheel，属未装而非装不上

<!-- 20260918-042 -->

## 手台自身刻意未改（用户当日决定「不管它了」），实测痛点供日后重估

每次调用固定约 2.4s（裸解释器 139ms，其中 orjson+httpx+pydantic 导入约 0.9s）且一个进程只发一个请求；`req` 输出里 `validated` 是整份信封的回声，实测 1302 字符中 608 字符（47%）为重复内容；probe 单次采样、无中位数
