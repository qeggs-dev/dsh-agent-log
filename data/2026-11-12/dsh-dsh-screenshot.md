<!-- 20261112-001 -->

## capture_screen 扩展为「整屏 / 单窗口」二选一

新增两个**互斥**参数 `pid`（integer）与 `name`（映像名称 string，`.exe` 可带可不带、不区分大小写、禁止通配符与路径）；都不给＝整屏。

给任一时只截该进程的**可见顶层窗口**，`PID 不存在 / 没有匹配映像 / 没有可见窗口 / 唯一窗口已最小化 / 尺寸无效` 一律工具报错且**不写文件**（实测 `name=svchost` 得「没有找到映像名称为 svchost 的可见窗口」，`screenshots` 目录无新文件）。

### 实现

截屏逻辑移到随包分发的 `dsh-screenshot\capture.ps1`（`files` 已加 `capture.ps1`），Node 侧只做参数校验、路径边界与 `& '<ps1>' -Output ... [-ProcessId N|-ImageName 'x']` 调用，结果走 `SCREENSHOT_OK <w> <h> <bytes> <base64(json)>` / `SCREENSHOT_ERROR <base64(中文原因)>` 单行标记。

### 窗口选择的两个坑

①**按映像名必须窗口优先**——`Get-Process -Name` 会漏掉当前令牌枚举不到的进程（本机 DSH 主进程 pid 59388 的 `SessionId` 为空、不出现在 `Get-Process` 列表里，但 `Get-Process -Id` 与 `Process.GetProcessById(pid).ProcessName` 都能读到），所以先 `EnumWindows`、再用窗口属主 PID 反查进程名比对；

②**PrintWindow 失败的真实原因是完整性级别，不是 Chromium 不支持**：沙箱内 pwsh 是 **Low 强制完整性**（`whoami /groups` 实测 `S-1-16-4096`），UIPI 拦掉发往正常窗口的 WM_PRINT（连 `Get-Process -Id 59908` 都读不到 SessionId/Path），所以 `PrintWindow` 返回 false、位图纯白；

**改成 `danger-full-access` 后进程是 Medium（`S-1-16-8192`），同一调用对 DSH 与 VS Code（都是 Electron）都返回 true、内容正确**，故窗口模式现在固定以 `danger-full-access` 执行（这也是它必须审批的原因）。

③**不再静默退回遮挡画面**：新旧 flag 都失败时先做遮挡采样（`WindowFromPoint` + `GetAncestor(GA_ROOT)` 打 4×4 网格），只有窗口**未被遮挡**才允许 `CopyFromScreen` 兜底，被遮挡直接报错。

### 验收

VS Code 窗口（pid 29452、2560×1400）被 DSH 窗口完全盖住时，`capture_screen({ name: "Code" })` 仍得到只有 VS Code 的干净画面（`method=print-window`，与全权限探针同为 322746 B）；

另测 `name="DeepSeek Harness"` 与 `pid=59908` 均正常、都先过审批。

<!-- 20261112-019 -->

## capture_screen 增加 cursor 参数（…

`capture_screen` 增加 `cursor` 参数（默认 true，传 false 关闭）：截图时把会话鼠标指针画进图里。

`PrintWindow` 与 `CopyFromScreen` 都不带光标，所以用 `GetCursorInfo` 取光标句柄与屏幕坐标、`GetIconInfo` 取热点，再 `Graphics.DrawIcon`（`Icon.FromHandle` 包装，绝不 Dispose/Destroy 共享光标句柄）按「屏幕坐标 − 原图原点 − 热点」画；

屏幕模式光标可见就画，窗口模式还要求 `WindowFromPoint` 的根窗口就是目标窗口（截被遮挡窗口时不会假装指针在它上面），meta 里的 `cursor` 如实反映这次到底画没画。

### 实测

整屏 2560×1440 在 (2178,941) 画出手形指针；`-ImageName 'DeepSeek Harness'` 得 cursor=true 且图里能看到手形光标（约 980,553），同一时刻 `-ImageName 'Code'`（被 DSH 挡住）为 cursor=false。

**坑**：`DrawIcon` 画进 32bppArgb 位图后 alpha 正常（保存的 PNG 仍不透明），但热点偏移必须减掉，否则光标整体偏 16px。

### 返回坐标

同日追加：结果里另有 `mouse: {x, y, inside}`（指针可见时才有；即使 `cursor: false` 也返回），**x/y 一律是系统屏幕坐标**（多显示器也以它为准；

全屏图取 VirtualScreen 包围盒、左上角可能为负，坐标也不偏移），窗口模式另在 `mouse.window` 给相对窗口左上角（DWM 外框）的坐标；x/y 是光标热点位置而不是图标左上角，`inside` 表示是否落在画面内，窗口被挡住时仍返回坐标但 `cursor=false`。

实测窗口 `mouse=(2220,1011)`、`mouse.window=(1888,838)`，差额正好是窗口原点 (332,173)；整屏同一次为 (2148,980)。

### 理由参数

同日追加：`capture_screen` 新增**必填** `reason`（string）：说明为什么截这张图，会原样进审批卡片的 `displayReason`（`…？

### 原因

<reason>`）与内部 `reason`（末尾 `(reason: <reason>)`）；空串/纯空白与超过 500 字符在 `execute` 里直接报错；会话已是 `danger-full-access` 时不弹卡，但理由仍随工具调用记进会话日志。它只影响审批文案，不写进 PNG。
