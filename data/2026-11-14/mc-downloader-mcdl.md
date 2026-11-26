<!-- 20261114-026 -->

## mcdl **发布 0.2.0**（用户要求提升版本号以便区分新旧包）

### 改动

package.json version 0.1.0 → **0.2.0**，README 打包段的产物名同步为 `MC-Downloader-0.2.0-Setup.exe`。

### 此版包含

GDL 第三个下载后端（三段长条按钮 GDL/ADL/直接、-pps 事件进度、跨源分片、重定向端点过滤、60s 卡死兜底）、右下角任务提醒、服务端启动脚本（.cmd/.sh/.command）、Java 无硬编码探测与缓存、跨平台 java 可执行名。

### 产物

`D:\Projects\MC-Downloader-build\MC-Downloader-0.2.0-Setup.exe`（106.40 MB，FileVersion/ProductVersion=0.2.0，CompanyName=MC Downloader，SHA256 `94eb0f8e4898de0c6951a7e0919427e61b875597ed1a8495d70384b5d427ca23`）+ blockmap；

`win-unpacked` 368 MB；打包后 smoke exit 0；asar 内部 version 已确认为 0.2.0（无 0.1.0 残留）。旧的 0.1.0 安装包已删，避免同名混淆。

<!-- 20261114-027 -->

## mcdl 的构建产物已按**工作区约定**归位（用户要求「构建能…

mcdl 的构建产物已按**工作区约定**归位（用户要求「构建能不能遵循一下工作区约定」，指 AGENTS.md「其他工作区」+ 记忆 20261101-003/005）：新建 `G:\work\projects\mcdl\{out,run}`，把 0.2.0 全套产物从 `D:\Projects\MC-Downloader-build` 移到 **`G:\work\projects\mcdl\out\`**（`MC-Downloader-0.2.0-Setup.exe` 106.4 MB、blockmap、`win-unpacked\`、builder-debug.yml），旧目录已删；

`run\` 预留给「可执行副本 + 独立 userData」（GUI 测试用）。新位置 smoke exit 0，哈希不变（`94eb0f8e…`）。

今后构建命令固定为 `electron-builder --win nsis --config.directories.output=G:\work\projects\mcdl\out`；README 打包段已同步（含 out/run 与第二工作区只做实验场的说明；

旧示例路径 D:\build\mcdl-out 已换掉）。

<!-- 20261114-028 -->

## mcdl 新增**窗口大小/位置记忆**（用户要求「记住上一次窗口大小」）

### 实现

`src/core/window-state.ts`（纯函数：`normalizeWindowState` 夹最小尺寸 1000x640、坐标在屏幕外就丢掉、保留 maximized；`windowStateFromBounds`；

`isPositionOnScreen` 支持多屏与负坐标），主进程读写 `%APPDATA%\MC Downloader\window-state.json`（不污染 settings.json）：启动时读并应用（含 `screens.getAllDisplays()` 工作区校验），resize/move/maximize/unmaximize 防抖 500ms 保存，close 时再存一次；

最大化时存 maximized 标记 + `getNormalBounds()` 还原尺寸，下次启动先建窗再 maximize。单测 115 → **122**（`test/window-state.test.ts` 7 项）。

### 实测

初始 1240x820 → SetWindowPos 到 1100x700 @ (140,110) → 关窗 → json 精确保存这四个值 → 重启恢复 1100x700；最大化后再关窗 → json `maximized:true`（正常尺寸仍保留 1240x820）→ 重启 IsZoomed=True。

测试后已删掉状态文件恢复默认。

安装包重打（含本功能）：`G:\work\projects\mcdl\out\MC-Downloader-0.2.0-Setup.exe` 106.40 MB，SHA256 `ff52a2d0032d712b740f06f2953a9ef5118dc21c9a514ab3c62c6ac86c34b6be`；

README 顶部功能列表已补一条。
