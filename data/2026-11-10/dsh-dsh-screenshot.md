<!-- 20261110-004 -->

## 新增桌面插件 @local/dsh-screenshot…

新增桌面插件 **`@local/dsh-screenshot`（整屏截图）**（源目录 `〈工作区〉/dsh-screenshot`，bundle 行 id `screenshot` / entry `include:screenshot`，`install_bundle` → `application: applied`、warnings 空）：唯一能力是一个模型工具 `capture_screen`（**没有 GUI、没有 HTTP 端点**），截取 **Windows 虚拟屏幕**（`SystemInformation.VirtualScreen`，含所有显示器）一次并存成 PNG。

参数只有可选 `path`（工作区内相对路径，必须仍在工作区内、只接受 `.png`；默认 `screenshots/screen-<YYYYMMDD-HHmmss>.png`）。

### 提权

先 `ctx.sandboxPolicy.resolve({ session })`，`mode !== 'danger-full-access'` 时走 `ctx.approval.request`（双语 `displayReason`，卡片写明目标绝对路径），只有 `allowed-once` 放行；

rejected / cancelled / unavailable / 无 approval 服务 / 无 agent 一律 fail closed。

### 执行

截屏命令交给 `ctx.shell.resolve/execute`（`sandboxPolicy` 用会话策略，`read-only` 只抬到 `workspace-write`；

20 s 预算、`onExpiry:'kill'`），脚本是 PowerShell + .NET 的 `Graphics.CopyFromScreen` + `Bitmap.Save(Png)`，目录由脚本 `New-Item -Force` 创建；成功后 Node 侧 `stat` 复核非空。

### 踩到的坑

工具定义上的 `timeoutMs` **会把等审批的时间算进调用预算**，首版 20000 ms 导致审批还没点就 `tool call timed out after 20000ms`（日志里 `approval/asked` → `decided: cancelled`）；

去掉工具级 `timeoutMs` 后只保留 shell 步骤的 20 s 预算，审批可无限等——**改 Host 插件模块必须重启 DSH**（loader 用裸 `import()`，ESM 缓存不失效，`set_plugin` 关开也没用）。

### 验收

重启后 `capture_screen()` 触发审批卡并 `allowed-once`，落盘 `screenshots\screen-20261110-163240.png`（2560×1440、1217185 B），`read_image` 确认是真实桌面；

会话日志里 `approval/asked`（toolName=`capture_screen`）与 `approval/decided`（`allowed-once`）成对存在。
