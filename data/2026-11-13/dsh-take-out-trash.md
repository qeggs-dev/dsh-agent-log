<!-- 20261113-010 -->

## 新增 DSH 插件 @local/take-out-tra…

新增 DSH 插件 **`@local/take-out-trash`（回收站删除）**（源目录 `〈工作区〉/take-out-trash`，bundle 行 id `take-out-trash`，desktop profile，`install_bundle` 以本地目录装入返回 `application: applied`、warnings 空，entry `include:take-out-trash` active，未声明 Config（status absent））。

只提供一个模型工具 **`trash`**（`paths: string[]`，1–200 项，绝对路径或相对会话工作区；

重复项按解析后的绝对路径合并）：把文件/目录移入系统回收站（Windows 回收站 / macOS 废纸篓 / Linux freedesktop 回收站），而不是永久删除，返回每项 `status` ∈ trashed / unverified / failed、`kind`、`bytes`。

### 校验是全有或全无

任一路径不存在则一项都不动；移动阶段的单项失败逐项报告。

**核心发现（决定了权限设计）**：DSH 的 Windows 文件沙箱进程是 **Low 完整性**，写不进 `$Recycle.Bin`，此时 `SHFileOperation(FOF_ALLOWUNDO)` **返回 0 却把文件永久删除**（探针实测：沙箱内 rc=0、文件消失、回收站无 $I 记录；

同一操作在沙箱外 High IL 则正常产生 $I/$R 对）。

因此本插件**故意用 `danger-full-access` 执行回收**（`ctx.shell` + `sandboxPolicy.mode = 'danger-full-access'`），并**自己强制边界**：只接受会话工作区内的路径（用 `realpath` 检查，junction/链接的真实路径逃出工作区也算界外）；

工作区外、以及 read-only 会话里的路径先经 approval 逐次批准（拒绝/取消/无通道则不动任何文件）；工作区本身、其上级目录、卷根一律拒绝。`inject` 只声明 `tools`，Windows 执行时才 `ctx.get('shell')`。

**Windows（`trash.ps1`）**：请求以 JSON 临时文件传入（不走命令行，避开 32K 上限与引号/中文问题），先做拒绝式预检——`NoRecycleFiles` 策略（HKCU/HKLM）、按卷 GUID 查 `BitBucket\Volume\*\NukeOnDelete`、非固定盘（网络/可移动）、单项超过 `MaxCapacity`（MB，>1e9 视为未设）——全部通过才逐个 `SHFileOperation`（`FOF_ALLOWUNDO|FOF_SILENT|FOF_NOCONFIRMATION|FOF_NOERRORUI`，flags 0x454）。

删除后用当前用户 SID 目录下的 `$I` 索引**逐项核对**：v2 格式头部 8+8+8 字节后是 4 字节字符数，路径从偏移 28 起 UTF-16LE（v1 从 24），比对原路径 + 删除时间 ≥ 批次开始；

找到 → `trashed`，找不到 → `unverified`（明确写「已移除但未确认进入回收站」）。输出 `TRASH_OK <base64 json>` / `TRASH_ERROR <base64 文本>`，两者都 exit 0（避免 stderr 读不到）。

**macOS / Linux**：macOS 先 `osascript` 让 Finder delete 并复查路径，再用 `〈用户目录〉/.Trash` 同卷移动兜底；

Linux 直接按 freedesktop 规范写 `.trashinfo`（`Path` / `DeletionDate`，跨卷用 `<topdir>/.Trash/<uid>` 或 `<topdir>/.Trash-<uid>`，Path 相对 topdir）并移入 `files/`。

两者**均未在本机实测**（本机只有 Windows）。注意 Node `lstat` 把 junction 报成 directory，所以真实路径逃出工作区的 junction 会走审批而不是直接删。

**验证（2026-11-13）**：12 项单测全过（参数校验、scope/approval 矩阵、freedesktop 记录与 mount 表解析、报告对齐、渲染）；

真实会话里两次调用把 4 个文件 + 2 个目录移入回收站，独立扫 `$I` 确认 `$R` 负载存在，随后把测试条目从回收站删掉、临时目录清理干净。

### 修过的两个缺陷

①`a.txt` 与 `sub/../a.txt` 解析后同路径会被处理两次（第二个报 rc=2，且按 path 覆盖导致成功项也被标成失败）——改为解析后去重，报告行按请求顺序对齐、路径查表只作兜底；②首版把删除结果按 path Map 覆盖，重复 path 全取最后一行。

### 测试坑

本机受限令牌下 `node --test tests/` 会 `spawn EPERM`（运行器起子进程要命名管道），必须 `node tests/trash.test.mjs` 在主进程里跑。

插件清单的标题/描述/图标已导出（`locale/en.json`、`locale/zh.json`、`icon.svg` 772B，XML 与格式校验通过），**插件页渲染未验证**（无浏览器控制）。

（2026-11-15 更新：该工具此后另要求必填 `description`，并把模型可见文案改成英文，见 id:20261115-008。）
