<!-- 20261020-001 -->

## 新增项目 **PCML（Py Console Minecraft…

新增项目 **PCML（Py Console Minecraft Launcher）**：定位是**Python 包而不是应用程序**——无 GUI、全异步、最终以 `pipx` 安装后用命令行操作（用户原话「主要是为了与程序互动」）。

起于 2026-10-20 用户提出「一起合作制作一个 MC 启动器」，当时工作区里**还没有任何代码**（「我还没开始写呢」），故是从零起的新仓库，与已有的 `mod-audit`（静态冲突分析器）是两个独立项目

<!-- 20261020-002 -->

## PCML 的既定技术选择（用户口述，**无依赖底线、以快速开发为优先**）

HTTP 用 `httpx`、CLI 用 `typer`（async 只在命令入口 `asyncio.run` 一次，命令本身同步）、进度用 `rich` 的 `Progress`（每文件一个 task + 一个总 task）、状态目录放 `%LOCALAPPDATA%`（pipx 下 cwd 随机，状态不能跟着 cwd 走）；

日常开发用 `pip install -e .`，只在验收时 `pipx install .`。PyPI 的 `pcml` 名称 2026-10-20 实测 **404（未占用）**

<!-- 20261020-003 -->

## PCML 的**分工**

主体框架由用户本人写，部分任务委托给我，他明确会分派但截至 2026-10-20 尚未派第一件。第一刀范围已定为**下载器**（「首先从下载器开始，要能解析，列出版本列表，并下载对应的资源」）。

我提出、**用户尚未表态**的两条建议：①把「解析/求解」与「下载」拆成两层，中间只过 `DownloadTask(url, dest_path, sha1, size, group, optional)`；

②四条硬约束——sha1 幂等跳过、原子落盘（临时文件 + rename）、并发按 host 限流、进度必须聚合（total = Σsize）

<!-- 20261020-004 -->

## PCML 技术栈已定（用户 2026-10-20 口述）

`orjson` + `pydantic` + `httpx`。

形态仿 poetry——**在工作目录下调用、自动加载配置**，三层各管一件事：全局配置 `%APPDATA%\pcml\config.toml`（用户要求放用户文件夹，跨平台用 `platformdirs`：`user_config_dir` / `user_cache_dir(appauthor=False, opinion=False)`；

注意它默认会给 cache 路径加一层 `Cache`）；全局缓存 `%LOCALAPPDATA%\pcml\Cache`（用户明确要「按全局配置缓存已下载内容，下次安装不再重下」）；项目目录 `./.pcml`（`config.toml` + `lock.json` + 实例内容）。

命令面对应 poetry：`pcml versions` / `lock` / `install` / `run`，其中 `lock.json` 是解析层与下载层之间的契约（`pcml install` 只认 lock、可离线）

<!-- 20261020-005 -->

## PCML 的两条技术判断（我提出，用户未反驳也未确认）

①pydantic v2 的 `model_validate_json` 是单遍 Rust 解析，先 `orjson.loads` 再 `model_validate` 反而两遍更慢——故读进模型走 pydantic、写和不需要建模的地方走 orjson；

②缓存里 assets 的 key 用 sha1（`objects/<前2位>/<sha1>`，与 Mojang 布局一致），libraries 的 key 用 **maven 路径**而非 hash（classpath 按坐标算）；

命中不等于可信（默认比 size、`--verify` 才算 sha1）、写入必须临时文件+`os.replace` 原子、缓存只增但要能 `pcml cache clear`，且**缓存目录必须可覆写**（默认落在 C 盘，一个版本全量是 500 MB 级）。

另：我建议资源**不复制进项目**、启动时 classpath 与 `--assetsDir` 直指缓存，此条用户未表态

<!-- 20261020-007 -->

## PCML 下载器的**并发参数语义由用户本人在 2026-10-…

PCML 下载器的**并发参数语义由用户本人在 2026-10-20 定义**（覆盖我原先按字节解读的猜测）：`largest_subtask` = **单个资源最多开几条连接**（不是分片字节数），`max_concurrent_resource` = **同时并行的资源个数**，故最坏连接数 = 两者乘积（默认 64 × 16）；

用户同时明确「下载器**只需要把结果扔出去**」——不落盘、不做 sha1 校验、不算原子写入，那属于调用方。落点 `〈项目目录〉/PCMLauncher/pcml/downloader/downloader.py`，`download()` 的多资源层与 `_sub_task()` 的单资源层都按此实现

<!-- 20261020-008 -->

## 本机外网**吞吐极低但连接数不受限**（2026-10-20 实…

本机外网**吞吐极低但连接数不受限**（2026-10-20 实测，python.org 直连）：单条 HTTPS 连接约 **12.5 KB/s**，并发 8 条约 110 KB/s（随并发上升），n=1/2/4/8 全部成功、无连接被拒——故「下载慢」不能诊断成 TCP 连接数限制；

11 MB 级文件在此链路上要数分钟，30 秒读超时会被真实触发。给 PCML 做下载测试应改用回环自建服务器（`ThreadingHTTPServer` + 手写 Range），不要依赖外网

<!-- 20261020-009 -->

## PCML 下载器的**输出形状由用户定**

`download()` 收 `url` 或 `(url, BinaryIO)`，target 是**调用方自己打开的**二进制流（磁盘文件或 `io.BytesIO`），下载器只按 offset `seek`+`write`、**绝不 close**；

写入是**缓冲写**——每个分片各攒够 `buffer_size`（默认 1 MiB）再落一次，峰值内存 ≈ buffer_size × 在飞分片数。同时 `download()` 仍 yield `(url_index, 分片号, 数据, offset)`，**顺序不保证**。

URL 队列**惰性消费**（N 个 worker 共享同一个迭代器，拿不到空位就不创建资源），故百万级队列的常驻协程数不随队列长度增长

<!-- 20261020-010 -->

## PCML 下载器代码结构（用户要求「逻辑简单、复杂逻辑搬出去、不…

PCML 下载器代码结构（用户要求「逻辑简单、复杂逻辑搬出去、不要常量表、全部写成参数」）：`pcml/downloader/` 下 `downloader.py`（只做编排）、`transfer.py`（唯一碰 HTTP：探测/单流/分段+续传重试/缓冲写）、`ranges.py`（纯函数：Content-Range 解析与分片规划）、`merge.py`（把多个 async generator 合成一条流，两层并发共用它）。

回环测试脚本在 `〈临时目录〉/pcml-test/test_downloader.py`（20 项，`ThreadingHTTPServer` 手写 Range/断连/超时/503 场景），用工作区 venv `〈工作区〉/.venv` 跑

<!-- 20261020-006 -->

## PCML 砍掉「异步控制台接口」（用户 2026-10-20 一…

PCML 砍掉「异步控制台接口」（用户 2026-10-20 一句「算了」否决，未给理由），改为要求一个**「能同时显示多行并刷新」的命令行界面**。

相关实测结论（我提出）：Windows 的 ProactorEventLoop **不支持 async stdin**（`connect_read_pipe(sys.stdin)` 直接 `NotImplementedError`），故子进程 stdout/stderr 可真异步、键盘输入只能走线程；

`child.terminate()` 在 Windows 上是 `TerminateProcess` 硬杀，服务端场景必须先经 stdin 发 `stop`；

「多行刷新」用 `rich` 的 `Progress`/`Live` 即可，但**行数必须有上限**（5000 个 asset 不可能每文件一行），非 tty 时必须降级，且库本身不该 `print`——进度属于 CLI 层，核心通过 `on_event` 回调注入
