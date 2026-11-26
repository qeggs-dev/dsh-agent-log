<!-- 20261021-001 -->

## 新增项目 AD Downloader 于 〈工作区〉/…

新增项目 **AD Downloader** 于 `〈工作区〉/adl/`（TS + Electron 44 + esbuild，UI 无框架）：多资源分片并发下载器，任务包为 ADv1 JSON。

核心层 `src/core/` 不依赖 Electron（ranges / net / transfer / scheduler / sink / state / taskfile / engine），27 项 `node --test` 单测全过；

端到端实测下载回环资源 64 MiB + 32 MiB（每 2 MiB 被掐断一次）+ 8 MiB（不支持 Range），三个文件字节数全对，64 MiB 那份的 SHA-256 前缀 `0ff4d6c068be2463` 与服务器一致。

`node build.mjs` 产出 `dist/main.cjs` / `preload.cjs` / `ui.js`

<!-- 20261021-002 -->

## AD Downloader 的三参数语义（用户定义）

`G`=最大并发量（全局硬上限，一切以它为准）、`R`=最大并发资源数、`P`=最大资源并发数；**单资源上限 = min(P, floor(0.8 × G))**，即单个资源最多吃 80%、留 20% 给后来者。默认 256/16/32。`P` 只在探测阶段决定切几片，运行中改只影响在飞连接数、不重切分片；

`G` 与 `R` 可实时生效

<!-- 20261021-003 -->

## AD Downloader 任务包（ADv1）的三处刻意设计

①`ver` 必须是字面量 `"ADv1"`，不匹配直接拒绝；未知字段一律忽略（向前兼容）。②资源可选 `dest`（绝对路径，或相对任务文件目录），**一旦出现必须由用户在界面上确认绝对路径才开工** —— 任务包是外部输入、能指向任何位置，程序不做路径白名单。

③续传状态写 `<目标文件>.state.json`（url + etag + size + 分片边界，任一对不上就重头来），**绝不写回任务包**

<!-- 20261021-004 -->

## 本机启动 Electron 应用的两个坑（实测，不是配置问题）

①DSH 会把 `ELECTRON_RUN_AS_NODE=1` 注入进程环境（User/Machine 层均无此变量），于是 electron.exe 被当纯 Node 跑、`require('electron')` 返回 exe 路径字符串，症状是主进程 `Cannot read properties of undefined (reading 'setAppUserModelId')`；

②从 DSH 受限令牌启动时 Chromium 子进程沙箱创建失败 —— GPU 侧报 `GPU process launch failed: error_code=18` → `FATAL: GPU process isn't usable. Goodbye.`（退出码 -2147483645），渲染侧表现为窗口能开但 `did-finish-load` 永不触发、CDP 的 `Runtime.evaluate` 无回应。

`app.disableHardwareAcceleration()` 与 `--disable-gpu-sandbox` 都只修 GPU，**只有 `--no-sandbox` 能全通**；

正常桌面启动不受影响，故未写进代码，只在 `AD Downloader.cmd` 里清掉 ELECTRON_RUN_AS_NODE

<!-- 20261021-005 -->

## npm 11.19 默认不执行依赖的 install scr…

npm 11.19 **默认不执行依赖的 install script**（输出 `npm warn install-scripts ... not yet covered by allowScripts`），故 `npm install` 之后 Electron 与 esbuild 的二进制都不存在；

手动补跑 `node node_modules/electron/install.js`（先设 `$env:ELECTRON_MIRROR='https://npmmirror.com/mirrors/electron/'`）与 `node node_modules/esbuild/install.js` 即可，不必改 npm 全局配置。

另：`node --test test/` 在 Node 24 下不再展开目录，必须写成 `node --test "test/*.test.ts"`

<!-- 20261021-006 -->

## AD Downloader 打包链路已跑通

`npm run dist` = make-icon → build → `electron-builder --win nsis`（electron-builder 26.15.3 + Electron 44.9.2），产物 `out\AD-Downloader-0.1.0-Setup.exe`（106.4 MB）与 `out\win-unpacked\`。

### 关键取舍

三个代理包已被 esbuild 内联进 `main.cjs`，故从 `dependencies` 移到 `devDependencies` 并让 `dependencies` 留空，asar 内只有 `dist/` + package.json；

若留在 dependencies，electron-builder 会把整份 node_modules 塞进 asar。图标 `build/icon.ico` 由 `tools\make-icon.mjs` 用自写的 PNG+ICO 编码器生成（不引图像库，6 档尺寸）。

安装包**无代码签名**，首次运行会被 SmartScreen 拦。

### 验证方式

`out\win-unpacked\AD Downloader.exe --smoke-check --no-sandbox` 输出 `SMOKE_OK`，即证明 asar 内 preload/UI 路径正确；**注意 asar 内容不能用字符串搜路径来抽检**（内部用反斜杠分隔，会误报 MISSING）

<!-- 20261021-007 -->

## AD Downloader 资源新增 path 字段（相对下…

AD Downloader 资源新增 `path` 字段（相对下载目录的子目录，如 `images/2026`）：`dest` 优先于 `path`，且**只有 `dest` 需要用户确认**（`path` 由构造保证跑不出下载目录）。

### 三道防线

①`validateRelativeDir` 逐段词法校验（拒绝以分隔符开头含 `//`、盘符含单字母 `a:b`、任何 `..`、Windows 非法字符、保留设备名、某级以点或空格结尾、超 32 层）；②`resolveInside` 用 `path.resolve` 兜底确认结果在根目录之下；

③建好父目录后 `realpath` 复核，挡住"下载目录里事先埋伏一条指向外部的目录联接/符号链接"——实测用 `fs.symlink(dir, link, 'junction')` 可复现，Windows 上建 junction 不需要管理员权限。

另：去重键已从"文件名"改为"完整路径"，不同子目录里的同名文件不再互相改名成 ` (1)`。

### 语义细节

整串**首尾**空白会被 `trim()`（粘贴常带空格），但**中间某级**以点或空格结尾仍然拒绝。测试从 27 项增至 38 项，端到端已验证 `videos\`、`videos\flaky\`、根目录三种落盘位置

<!-- 20261021-008 -->

## AD Downloader 界面重做为无边框窗口 + 自绘窗…

AD Downloader 界面重做为**无边框窗口 + 自绘窗口三键**（`frame:false` + `thickFrame:true`，IPC `adl:win-minimize|toggle-maximize|close|is-maximized` + 最大化状态反向推送），这是让应用顶栏与窗口按钮同一行的唯一办法；

边缘拖拽缩放、阴影、Aero Snap 仍由 Windows 原生处理（本机是 Win10 19045，Win11 的贴靠布局磁贴本来就没有，故自绘无实质损失）。内容块为半透明玻璃卡片（`backdrop-filter`），从屏幕外滑入、交错 70ms，**顶栏是唯一不动画的块**并垫了一层淡暗角保证亮背景下可读；

`prefers-reduced-motion` 时全关。

### 背景图链路

主进程 `nativeImage` 解码 → 长边 ≤2560 → 转 JPEG 存 `<userData>\background.jpg` → data URL 给渲染层，可调模糊 0–24px / 暗化 0–85% / 填充 cover|contain|stretch|tile；

`Menu.setApplicationMenu(null)` 去掉原生菜单。日志默认折叠成底部一行、**出错自动展开**

<!-- 20261021-009 -->

## 本机验证 Electron 界面的两条实测事实

①`webContents.capturePage()` 在关闭硬件加速后返回 `UnknownVizError`、截不出图，改用 CDP `Page.captureScreenshot`（工作区 `adl\tools\screenshot.mjs`，第四参数可传一个"截图前先求值"的表达式，用来把界面驱动到有数据的状态）；

②`nativeImage.createFromPath` **只认 PNG / JPEG**，BMP 解析出空 image（实测踩过，别再造 BMP 测试图），测试背景图改由 `adl\tools\png.mjs`（自写 PNG 编码器，make-icon 与 make-test-image 共用，不引图像库）生成

<!-- 20261021-010 -->

## AD Downloader 新增界面上新建任务包（新建…

AD Downloader 新增**界面上新建任务包**（`新建任务包` 按钮 → 玻璃弹窗）：任务名 / 全局代理 / 批量粘贴 URL（每行一个、可统一指定子目录）/ 逐行可改文件名与子目录 / 保存并载入。

拼接逻辑是 `src/core/taskfile.ts` 的 `buildTaskPayload(draft)`（故意放在核心层而非 main.ts，这样能单测）；

保存前**必须再过一遍 `parseTaskFile()`** —— 写文件用读文件那套校验器，所以不可能生成一个自己读不了的任务包（`path: "../../etc"` 在这一步被拒）。逐条资源的 `proxy` 不在编辑器里，只能改 JSON。测试 38 → 42。

### 同批改动

玻璃卡片 `--glass` 从 rgba(26,30,42,0.58) 降到 0.32、`--glass-strong` 0.82→0.56，backdrop blur 20→28px、saturate 150%→175%

<!-- 20261021-011 -->

## AD Downloader 做了分发加固（用户原话「至少…

AD Downloader 做了**分发加固**（用户原话「至少要分发的话对方不一定有我们这样的环境」）：①`app.requestSingleInstanceLock()` + `second-instance` 把已有窗口拉到前台，避免两个进程抢同一输出目录与 `.state.json`；

②`uncaughtException` → `src/main/log.ts` 记日志 + `dialog.showMessageBoxSync` 带「复制错误信息 / 打开日志 / 关闭」，随后 `app.exit(1)`；

`unhandledRejection` **只记账不弹窗不退出**（一个漏掉的 rejection 不该杀掉正在跑的任务）；③渲染进程 `render-process-gone` 也走同一路径；

④日志 `<userData>\logs\main.log` 用**同步** append（崩溃时异步队列不一定活着），超 2 MB 滚到 `main.1.log`，内容含启动环境、任务开始/结束、每个资源成败；

⑤设置里的 outputDir 不存在时自动回退 `app.getPath("downloads")` 并写回。

### 注意

默认输出目录本来就已经是系统的「下载」文件夹，之前界面上显示 workspace 路径是我用 CDP 驱动测试时写进 settings 的，不是代码默认值

<!-- 20261021-012 -->

## 上面第 ⑤ 条第一版写错了并当场被端到端抓到

最初在 start 里对「输出目录不存在」直接报错，而原来是靠 `ensureParentDir` 自动创建的，等于回归掉了自动化与新机器的路径。正确做法是 `mkdir(recursive:true)` 再报错。

### 教训

加"保护性校验"前先确认它保护的对象原本是不是会自动创建

<!-- 20261021-013 -->

## AD Downloader 玻璃卡片在 0.32 透明度的照片背…

AD Downloader 玻璃卡片在 0.32 透明度的照片背景上**边界看不清**，修法不是加深描边而是加**冷白光晕**：新增 `--card-edge: rgba(255,255,255,0.14)`（卡片专用描边，比通用 `--glass-line` 实）与 `--glass-glow: rgba(148,178,255,0.2)`，`.card` / `.logbar` / `.bg-panel` / `dialog` 统一为 `inset 顶部内高光 + 0 0 22~34px 光晕 + 原有黑色投影` 三层。

另：`tools/screenshot.mjs` 的 devtools 列表请求改成了**轮询重试**（应用启动慢时原来会直接 ECONNREFUSED）

<!-- 20261021-014 -->

## AD Downloader 界面卡的根因是 app.dis…

AD Downloader 界面卡的**根因是 `app.disableHardwareAcceleration()`**：那是早先为在受限环境里启动而加的，等于把所有 `backdrop-filter` 按到 CPU 上。

已删除，只保留 `disable-gpu-sandbox`（真正起不来的是 GPU 子进程沙箱）。

另加**无 GPU 自动降级**：启动后读 `app.getGPUFeatureStatus()`，`gpu_compositing !== enabled` 就给 `<html>` 打 `data-perf="lite"`，CSS 去掉 `backdrop-filter` 但**保留背景层静态模糊**（只栅格化一次，不是每帧开销）。

### 同批优化

去掉滚动容器吸顶表头的 backdrop-filter、进度刷新改为「值变了才写 DOM」、`backgroundThrottling: false`。本机实测（软件渲染）37.5 fps / p95 100 ms → 60.5 fps / p95 16.8 ms。

**这台机器 `webgl`/`gpu_compositing` 全是 disabled，没有可用 GPU，所以 GPU 路径在本地无法验证**

<!-- 20261021-015 -->

## AD Downloader 新增卡片自适应亮暗

把背景图按 CSS 同款填充规则画进 72px 宽的小 canvas（≈视口缩略图）读格点亮度，再按卡片 `getBoundingClientRect()` 取平均、叠上暗化层，超 0.42 切 `data-tone="light"`。

### 两个必踩的坑

①自定义属性会级联，但 `color` 继承的是**计算值** —— 只在卡片上重定义 `--text` 不够，必须同时在该元素写 `color: var(--text)` 才会重新求值（否则卡片里所有文字仍是 body 那套浅色，亮色模式下几乎看不见）；

②入场动画期间 `getBoundingClientRect()` 带 transform，量到的不是最终位置，必须等动画跑完再判。

另：Electron 的**后台节流**会把 setTimeout 压到 ~1Hz，导致脚本验证时读到上一步的结果（表现为「亮暗判定反了」），已通过 `backgroundThrottling: false` 解决

<!-- 20261021-016 -->

## 上条的补充（用户反馈「新建任务包页面没有适配亮色」）

**模态弹窗的明暗必须连 `::backdrop` 一起切**。只给 `dialog` 加 light 样式是不够的 —— 用户看到的背景是「背景图 × 暗化 × `::backdrop` 黑幕(0.6)」，永远偏暗，而且深色字会压在近黑幕布上。

### 做法

`applyTones` 的选择器加上 `dialog`，`dialog[data-tone="light"]::backdrop { background: rgba(226,232,244,0.6) }`（浅色纱），弹窗本体 `rgba(250,251,255,0.88)`、lite 模式 `0.95`；

`showModal()` 之后要 `scheduleTones(0)` 等一帧再判，因为关闭状态下 `getBoundingClientRect()` 全是 0。另 `.bg-panel` **有意保持深色**（它是调暗化的地方，跟着翻会在拖动时来回跳）

<!-- 20261021-017 -->

## AD Downloader 改为多任务组并发（用户定义

一个任务包 = 一个组，可多包并行）：新增 `src/core/manager.ts`（GroupManager 持有唯一的 `FairLimiter` + 组注册表），Engine 从单体降为"一个组"。

### 并发是三层

全局 G → 组 `min(limit, ⌊0.8G⌋)`（20% 留给新启动的组）→ 单资源 P。`FairLimiter` 升级为按 `(group, resource)` 排队、跨组跨资源轮转，三层任一撞顶就跳过该队列。任务包新增可选 `limit`（1–4096 整数，不填只受 0.8G 约束；

**ver 仍是 ADv1**，因为未知字段本来就会被忽略）。

### 组内按字节数加权

先并发探测全组（上限 8、且计入全局预算），再 `片数 = clamp(round(组上限 × 本资源字节 / 组总字节), 1, P)`；实测 64MB/32MB 分到 15 片/7 片。界面按组分段（组头行含 limit/上限/汇总/单独停止），「开始」每按一次新建一个组，新增「全部停止」与「清除已结束的任务组」；

顶栏徽标改为**软件版本** `v0.1.0`（原来那个 ADv1 是格式版本，容易误解）

<!-- 20261021-018 -->

## 上一轮踩的两个坑

①**验证多组总连接不能用「两个 loopback 服务器的 socket 峰值相加」**——keep-alive 池里的空闲 socket 也算连接，会得出 14 > G=10 的假超标；正确做法是采样 `manager.snapshot().activeConnections` 的峰值（限流器自己的在飞数）。

②原来标题栏只认"已载入的任务包"，脚本直接起组时会出现「未载入任务」却有两组在跑的怪现象 —— 已改成：有载入显示任务名，否则有组就显示「N 个任务组」

<!-- 20261021-019 -->

## 三个子代理对 AD Downloader 做了只读审计（渲染层…

三个子代理对 AD Downloader 做了只读审计（渲染层 12 条 / 主进程 10 条 / 核心链路 12 条），已修的高价值项：①**单流下载原本完全绕过 FairLimiter**（`#runWhole` 不 acquire），不支持 Range 的资源不受 G/组上限/P 任何约束 —— 现在与分段同样占 `res:<index>` 许可，并新增基于 loopback `maxActiveRequests` 的真并发测试（原来那个"总连接不超 G"的断言测的是 limiter 自己的计数器，近乎重言）；

②**跨组同名路径无互斥**（两个任务包撞名会互相截断/交错写却都标 done）—— GroupManager 增加规范化绝对路径租约 `claimPath`，显式 dest 冲突判失败、派生名自动加 ` (n)`；

③**dest 的"必须确认"可被渲染进程绕过**（`destAccepted` 是自报布尔）—— 确认移到主进程 `showMessageBoxSync`，顺带消掉 TOCTOU，同时删除渲染层的 destDialog；

④续传状态被无条件信任（无 fsync、`done` 可为 Infinity、文件被截断仍跳过）—— 加 `Sink.sync()`、readState 夹逼、resume 前 stat 核对；⑤206 响应起点超前于请求时整段错位、416 分支的"已完成"返回值被丢弃导致白重试；

⑥窗口加 `will-navigate` 守卫 + `setWindowOpenHandler` deny；⑦崩溃兜底去掉 80ms 抢跑定时器（原来会绕过 before-quit，manager.stop 与"退出"日志都不执行）；⑧渲染进程崩溃改为自动 reload，10 秒内反复崩才致命；

⑨settings 改原子写（temp+rename）+ 串行队列 + outputDir 绝对路径校验；⑩盘符根目录下 `resolveInside` 误判越界（改 path.relative）。测试 46 → 49

<!-- 20261021-020 -->

## 上述审计明确未修的项（不是遗漏，是取舍）

①续传不校验远端内容身份 —— `lastModified` 采集了却没写进状态、也不发 `If-Range`，服务端无 ETag 且内容变了但字节数不变时会拼出两代混合文件；②abort 监听器只 once 不摘除，长任务里线性累积会刷 `MaxListenersExceededWarning`；

③`start` 接受渲染层传来的任意 taskPath（无 pickTask 白名单），失败信息还能区分 ENOENT/EACCES —— 但收紧会破坏 e2e/截图脚本的自动化调用；

④重试用例实际只覆盖了探测阶段的重试（503/429 被探测的 3 个 GET 吃掉了），`runChunk`/`runSingle` 的退避与 `parseRetryAfter` 无单测
