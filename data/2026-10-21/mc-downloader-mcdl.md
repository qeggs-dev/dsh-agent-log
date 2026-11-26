<!-- 20261021-021 -->

## 新增项目 MC Downloader（〈工作区〉/mcdl/）

列出 Minecraft 原版（Java）版本、算出文件清单，二选一——**导出 ADv1 任务包**交给 AD Downloader，或**自己下载**。用户当天先明确"直接下载＝软件自己下"，随后又明确**不要复用 ADL 的下载引擎**（见 032），所以下载器是自研的。

### 技术

TS + Electron 44 + esbuild，UI 无框架。

### 结构

`src/core`（sources / manifest / plan / **downloader** / task / verify）+ `src/main` + `src/ui` + `src/shared`；

38 项 `node --test` 单测全过，另加 `tools/check-task.mjs`（按 ADv1 的 hash 字典逐条核对）。**唯一剩下的 ADL 依赖**是 `src/core/task.ts` 里 `parseTaskFile()`（验收导出的包能不能被 ADL 读），下载路径零 ADL 代码；

`mcdl\node_modules` 是指向 `adl\node_modules` 的**目录联接**（同一批 devDeps，省掉一次 ~100 MB 的 electron 下载，不需要管理员权限）

<!-- 20261021-023 -->

## mcdl 对 ADv1 的三条硬规矩

①**只用 `path`、绝不写 `dest`** —— dest 是绝对路径，ADL 会要求逐条确认，几千个文件没法点；path 由 ADL 保证跑不出根目录。②导出前用 ADL 自己的 `parseTaskFile()` 验收，**落盘后再读回来解析一次**，所以不可能产出 ADL 打不开的包。

③每条资源带 `hash: {"sha1": "..."}` —— 这是 ADv1 的校验字段（见 ADL 那条 029），ADL 下载完会逐个验；**顶层 `sha1`/`size` 不是 ADv1 字段**（ADL 不读，只是未知字段）。

### 下载源策略

元数据（manifest / 版本 JSON / 资源索引 / logging 配置）**永远走官方**，镜像只接管大文件（库、资源对象、client/server jar）；

实测 `bmclapi2.bangbang93.com` 会 302 到 `bmclapi1x.sakura.sld.tw`，mcdl 自己的下载器跟跨源重定向（≤6 跳），所以镜像可用

<!-- 20261021-024 -->

## mcdl 实测数据（同日）

`26.3` 完整档 = 5225 个文件 / 614.7 MB（client 41.5 MB、库 74 个 87.8 MB、资源 5147 个 484.9 MB），只跑过 `--plan`；`1.12.2` 客户端 39 个文件 51.6 MB 用自研下载器 **6 秒**下完、39/39 sha1 命中；

`1.5.2` 完整档（legacy 索引、468 个资源）480 个文件 54.2 MB **10 秒**、480/480 sha1 命中；`1.12.2` 服务端走 BMCLAPI 30.2 MB **6 秒**；删掉 1 个库再下一次只调度 1 个。

**对照（同一批任务用 ADL 引擎）**：480 个文件 45 秒、39 个文件 14 秒 —— 差距主要来自 ADL 必须先探测全组再按字节加权分片（480 个文件约 35 秒只探不下），而自研下载器不分片、扫完目录直接开下，探测阶段整个省掉

<!-- 20261021-025 -->

## mcdl 抓到的真 bug（已修）

`1.12.2` 的 `net.java.jinput:jinput-platform:2.0.5` 只有 `downloads.classifiers`（natives）、没有 `artifact`，我按 maven 坐标推出了一个基础 jar → 下载时 HTTP 404 `The specified blob does not exist`。

### 规则

只有整个 `downloads` 块都缺失的真·老格式才允许按 maven 坐标推导；有 `downloads` 但没有 `artifact` 的条目是**纯 natives 库**，不能推基础 jar。单测补了这条断言

<!-- 20261021-026 -->

## mcdl 打包链路

`electron-builder --win nsis` 产出 `out\MC-Downloader-0.1.0-Setup.exe`（106.5 MB）与 `out\win-unpacked\`。

**必须在 package.json 的 build 里配 `"electronDist": "node_modules/electron/dist"`** —— 否则 electron-builder 会去下 150 MB 的 Electron zip，本机实测进度到 100% 后请求挂死、600 秒超时（`got` 报 `Timeout awaiting 'request'`；

其实 `%LOCALAPPDATA%\electron\Cache\...\electron-v44.9.2-win32-x64.zip` 早就在盘上）。另：命令行写 `-c.electronDist=...` 是错的（`-c` 是 `--config` 的别名，会被当成配置文件路径报 ENOENT）。

图标绿色调，复用 `adl/tools/png.mjs`。

### 验证

`out\win-unpacked\MC Downloader.exe --smoke-check --no-sandbox` 出 `SMOKE_OK`，且打包后的 exe 能跑 `--plan`。

CLI 共四个动作：`--plan` / `--export` / `--download` / `--smoke-check`，都不走单实例锁

<!-- 20261021-027 -->

## ADL 审计里明确延后的 4 项已全部处理（单测 50 → 57）

①**续传身份校验**——`.state.json` 增加 `lastModified`，`sameResource` 改为「etag 或 lastModified **至少一个两边都在且相等**」才允许续（原来是"任一侧 null 就当相同"，等于默认信任），续传请求带 `If-Range`，服务端回 200 即按整份重下；

②**abort 监听器**改为成功路径显式摘除（`net.ts` 用 `req.once("close")` 摘、`FairLimiter.acquire` 在 `grant` 时摘），不再依赖 `{ once: true }`；

③**`start` 加路径白名单**——main 记录 `pickTask`/`saveTask` 产生过的路径，其它一律拒绝，自动化用 `--allow-any-task-path` 显式放开；

④**真实重试测试**——loopback 新增 `failOnRangeGets`（只对探测之后的分段请求注入 503）与 `failGets`（精确指定第几个 GET 失败，用来打单流路径），新增 `test/net.test.ts` 表驱动覆盖 `parseRetryAfter`/`isRetryable`/`isRetryableStatus`，另加"重试耗尽判失败"用例

<!-- 20261021-028 -->

## ADL core 的公开 API 在本轮有多处破坏性变化，mcdl 直接 import 这些模块，升级后必须重新 typecheck

`ResolvedTask` 新增必填 `limit`（`number | null`）；`ResourceProgress` 新增必填 `parts`；

`RunSnapshot` 从单任务形状改成 `{ groups: GroupProgress[], budget, perResourceCap, activeConnections }`；

`Engine` 构造签名改为 `(task, outputDir, config, limiter, groupId, options)` 且不再产出快照（改用 `getResources()`），多组编排走 `core/manager.ts` 的 `GroupManager`；

`taskfile.parseTaskFile` 会拒绝**同一任务包里重复的 dest**；`state.ResourceStateFile` 新增 `lastModified` 字段（旧 state 文件缺这个字段 → 视为"身份无法确认" → 不再续传，会整份重下）。

**mcdl 当天晚些时候已改成自研下载器，只 import `taskfile.ts`，上述破坏性变化对它只剩 `parseTaskFile` 这一条**

<!-- 20261021-029 -->

## ADL 资源新增 hash 校验字段

`"hash": { "sha1": "...", "sha256": "..." }`，写几种验几种、**全部通过才算成功**。

实现在新模块 `src/core/verify.ts`：支持 md5/sha1/sha224/sha256/sha384/sha512，接受 `sha-256` 这类别名（归一小写无横线），解析阶段即校验算法白名单 + 摘要十六进制长度 + 同算法写两次（含别名）直接拒。

校验发生在下载全部完成之后，**一遍流式读盘**同时喂多个 hash 实例（写三种不会读三遍），期间资源状态新增 `verifying`（界面显示「校验中」）。失败时**文件保留**便于排查，但续传状态在验证前就已清掉——否则下次会接着一个已知错误的文件。

**注意 mcdl 之前写的是平铺的 `sha1`/`size` 字段，不是这个 `hash` 字典**，那些字段仍会被当未知字段忽略、不触发校验；要校验得改成 `hash: { sha1: ... }`。演示任务包的 `norange-8mb.bin` 已带 sha256 并在 e2e 里验证通过

<!-- 20261021-032 -->

## mcdl 的下载器改为自研流式（用户明确「不要直接复用…

mcdl 的下载器改为**自研流式**（用户明确「不要直接复用 ADL 的下载引擎」）：`src/core/downloader.ts`，不碰 Range、不分片、不续传；每个资源一条连接，**同时最多 16 个资源**（`MAX_CONCURRENCY` 硬上限，界面可调 1–16），在飞连接数 = 正在下的资源数。

落盘是 `GET → 写 <目标>.part → 边下边算 sha1、收完比 size → 全过才 rename`，所以不会留半截文件、也不需要状态文件；失败或取消会删 `.part`。

### 重试

网络抖动与 408/425/429/5xx 按 0.4s、0.8s 退避（默认 2 次），404 与证书错误不重试；跟随跨源重定向 ≤6 跳；取消走 AbortSignal，在飞与排队的一并标 cancelled。

### 为什么不分片

Minecraft 绝大多数是几 KB–几百 KB 的小文件，切片在这种尺寸上是负收益；唯一的大文件是 jar，它和其余文件本来就并行。11 项单测覆盖并发上限、302、503 重试、sha1/大小不符、abort、404 不重试、路径越界（总计 38 项）

<!-- 20261021-035 -->

## mcdl 新增 Fabric / Forge / NeoFo…

mcdl 新增 **Fabric / Forge / NeoForge 的下载与自动安装**（用户要求；源预设官方 + BMCLAPI）。

### 三条路

**Fabric 纯下载**（官方 profile JSON 本身就是启动器可用的 version JSON，照它拉库写 `versions/<id>/`，**不需要 Java**）；

**Forge / NeoForge 跑官方 installer**（`--installClient <根目录>`，必须用版本足够的 Java：1.17–1.20.4 要 17、1.20.5+ 要 21、26.x 要 25）。装之前都先补齐原版（jar/库/资源索引）。

### 界面

右侧「原版/Fabric/Forge/NeoForge」页签 + 加载器版本下拉 + Java 下拉（自动按"够用的最低版本"挑）+ 安装按钮；

### CLI

`--install-loader --kind ... --loader-version ... [--java ...]`。单测 38 → **53 项**（新增 loaders / zip 两组）。

### 实测

Fabric 1.20.1 13 秒、Forge 1.20.1 123 秒、NeoForge 1.21.1 220 秒，产物分别是 `versions/fabric-loader-0.15.11-1.20.1`、`versions/1.20.1-forge-47.4.10`、`versions/neoforge-21.1.209`

<!-- 20261021-036 -->

## Forge/NeoForge 安装的真实障碍与解法（本轮最关键的发现）

installer 下完文件后要跑一串 processors，其中 `DOWNLOAD_MOJMAPS` 会从 Mojang 现拉映射（就是版本 JSON 的 `client_mappings`），且**一次失败就整单回滚、没有重试**。

### 而本机

①**installer 启动子 JVM 时没有继承环境变量**（实测 `JAVA_TOOL_OPTIONS`/`_JAVA_OPTIONS` 只在 installer 自己那层生效，"Picked up" 只出现 1 次），所以给 installer 的 `-Djava.net.preferIPv4Stack=true` 到不了 processor；

②本机 **IPv6 路由不通**，Java 默认先试 IPv6 → 连 `piston-data.mojang.com` 15 秒超时（同一台机器的 Node 正常；带 IPv4 参数时 6/6 成功）。

解法是跑 installer 前**预置 + 手术**：读 installer 里的 `install_profile.json`，把它要的库与 mojmaps 先用我们自己的下载器下好（带重试与备用源）；

再在**本地缓存的 installer 副本**上摘掉 `DOWNLOAD_MOJMAPS` 处理器，并**移除 `META-INF/*.SF|*.RSA` 签名**——Forge 的包签过名，改了内容它会自检报 `A problem installing was detected`（NeoForge 的包没签名，本来就能改）；

改前留 `.original` 备份、改完用自己的 ZIP 读取器读回来验证，被拒绝就还原重试。做完之后两家安装都不再依赖 Java 侧对 Mojang 的可达性，一次成功

<!-- 20261021-037 -->

## mcdl 加载器的源可达性实测（决定"选哪个源"）

**NeoForge 官方 maven `maven.neoforged.net` 从本机完全连不上**（连接 42 秒超时，`neoforged.net` 也超时），而 `bmclapi2.bangbang93.com/maven/net/neoforged/neoforge/21.1.209/...installer.jar` 是 **200**（落到 mirror.nyist.edu.cn）——所以 NeoForge 只能走 BMCLAPI。

**Forge 的 BMCLAPI `/maven` 是"按需回源"的通用代理**：具体文件 200，但它的 `maven-metadata.xml` **停在 2022-02**（3839 条、`1.20.1-*` 命中 0），所以 Forge 的**版本清单必须用官方**、文件可以走镜像。

Fabric 两边都通（`/fabric-meta` 200，但 profile 里的库地址是**基址** `https://maven.fabricmc.net/`，要自己按 maven 坐标拼路径，镜像时替换成 `/maven/`）。

程序里默认官方优先、失败回退，并对"清单缺目标版本"明确报错，不拿 2022 年的清单去猜

<!-- 20261021-039 -->

## mcdl 新增「用 ADL 下载」（用户要求

加一个按钮，并明确**不要加 `-no-gui`**）。

ADL 新版已支持把任务递给正在运行的实例：第二个实例用**自己的 argv**（不被 Chromium 重排）解析成结构化请求，通过 `requestSingleInstanceLock(additionalData)` 递交，`second-instance` 里读 `additionalData.adlRequest` / `adlWait`；

带 `--wait` 时第二个进程会等这批跑完、再带退出码退出。

所以 mcdl 的调用是 `AD Downloader.exe --task <包> --out <根目录> [--r N] --wait`（**不带 `-no-gui`**），并且**必须用 exe**——`adl.cmd` 内部写死 `start /b /wait "%EXE%" -no-gui %*`，强制无窗口。

ADL 本来没开时，我们拉起的进程**就是**它的窗口，mcdl 只等 8 秒，拿不到退出码就报"已交给 ADL"并把收尾挂后台。

**交接时必须清 `ELECTRON_RUN_AS_NODE`**：ADL 也是 Electron 应用，带着这个变量会当纯 Node 跑、窗口一闪就没（本轮实测踩到，已写进 `spawnAdl` 的 env）。

### 探测顺序

设置 `adlPath` → `%LOCALAPPDATA%\Programs\AD Downloader` → `%ProgramFiles%\AD Downloader` → 同工作区 `adl\out\win-unpacked`。

实测（1.12.2 服务端 30.2 MB，ADL 已在运行）：mcdl 导出 → ADL 收到任务 → 下载并**按 hash sha1 校验通过** → 第二个实例退出码 0（`2/2 成功`）；GUI 按钮同样跑通。

单测 53 → **60 项**（新增 `test/adl.test.ts`：参数里不能有 `-no-gui`、必须带 `--wait`、退出码含义、探测、拒绝 cmd 模式）
