<!-- 20261018-003 -->

## 桌面版 DSH 的窗口几何壳层完全不记忆

`lib/main.js` 的 `createWindow()` 写死 `width:1280, height:820, minWidth:520, minHeight:600`，全文件没有 `window-state`/`getNormalBounds` 之类的回读逻辑（唯一的 `getBounds` 属于付费页子视图），壳自己的 `%APPDATA%\@deepseek-ai\dsh-desktop\desktop\settings.json` 只校验 `updates.allowTestAuthPopupWindow` 一个键。

改 `resources\app.asar` 不是可选项：`DeepSeek Harness.exe` 的 `ELECTRONASAR` 资源里嵌着完整性清单 `[{"file":"resources\\app.asar","alg":"SHA256","value":"487721b3…"}]`（Electron 的 asar 完整性 fuse），且 App 走 nightly 自动更新会覆盖补丁

<!-- 20261018-004 -->

## 已装 Host 插件 @local/dsh-window-…

已装 Host 插件 **`@local/dsh-window-keeper`**（工作区 `dsh_plugins\dsh-window-keeper\`（2026-11-13 迁入），桌面 profile，行 id `window-keeper`，`plugin_manager install_bundle` 安装）解决窗口记忆：用 Koffi 调 user32 找主窗口（类名 `Chrome_WidgetWin_1` + 无 owner + `WS_THICKFRAME` + 进程 exe 等于 `process.execPath`，据此排除 IME、托盘、`Chrome_WidgetWin_0` 与固定尺寸欢迎窗），用 `SetWinEventHook` 订阅窗口事件（全程不轮询）、**事件停下 3 秒后**才读 `GetWindowPlacement` 的 `rcNormalPosition`（最大化时仍是还原矩形）与最大化标志写入 `%APPDATA%\@deepseek-ai\dsh-desktop\desktop\window-state.json`（2026-11-14 起；

此前误放在插件目录内），启动时趁窗口仍隐藏（`show:false`）`SetWindowPos` 还原，之后 4 秒内最多纠正 3 次；状态文件只在启动时读一次，手工改它要等下次启动才生效。

### 实测已生效

应用 2003 与 2002 宽均成功（窗口矩形 330,183,2332,1274），诊断日志在 `window-state.json.log`。

### 实现要点

Koffi 必须用 `createRequire(<resources>\app.asar\dsh\package.json)` 解析（原生件在 `app.asar.unpacked`），koffi 结构体类型名要写进函数签名（写成 `RECT` 会报 `Unknown or invalid type name`）；

**Win32 钩子回调只投递给「自己取消息」的线程**，所以钩子装在 worker 线程里，用 `MsgWaitForMultipleObjects(0,null,false,INFINITE,QS_ALLINPUT)` 阻塞等消息、`PeekMessageW` 取空队列、再用 `setImmediate` 把控制权交回 JS —— 这样既不阻塞 Host 事件循环也不是轮询，Koffi 的回调会在 worker 的 isolate 里正常投递（实测自建窗口移动 5 次收到 5 个窗口级事件）

<!-- 20261018-006 -->

## 桌面版 DSH 的窗口能力位置（回答「框架能不能检测分辨率/尺寸变化」的根据）

Electron 主进程本来就有 `win.on('resize'/'move'/'maximize')`、`getBounds/getNormalBounds/isMaximized` 与 `screen.on('display-metrics-changed'/'display-added'/'display-removed')`，渲染进程有 `window.resize`/`matchMedia('(resolution: …)')`/`devicePixelRatio`；

**但 DSH 的 `lib/main.js` 一个都没订阅**，preload 只暴露 boot / directory picker / locale / updates / `dshPlatform`（付费页子视图）与 `window-fullscreen` 推送，**没有任何读写窗口几何的 IPC**；

Cordis 是插件/服务框架、没有 window/display 概念，插件又跑在 Host 子进程里摸不到 `BrowserWindow` —— 所以对插件作者来说这个能力等于不存在，只能走 Win32

<!-- 20261018-005 -->

## DSH 的 pwsh 沙箱子进程是低完整性 + 受限令牌…

DSH 的 pwsh 沙箱子进程是**低完整性 + 受限令牌**，跨进程 `SetWindowPos` 对它返回 `Win32 5（拒绝访问）`（UIPI）；同一操作由 **Host 进程**（中完整性、无受限令牌）执行则成功。所以「从插件里改桌面窗口」可行、从 `pwsh` 工具里改不可行，验证时要认准是哪个进程在做
