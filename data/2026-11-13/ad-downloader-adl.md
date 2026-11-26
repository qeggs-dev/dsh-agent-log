<!-- 20261113-005 -->

## ADL（AD Downloader）现状速览（2026-11-13 核对仓库）

位置 `〈工作区〉/adl/`，版本 0.1.0，TS + Electron 44 + esbuild，UI 无框架；

源码 20 个 TS 文件约 6872 行，7 个测试文件（cli / engine / net / ranges / sourcepool / taskfile / verify），最后一次验证为 2026-11-01 的 **127/127 通过**；源码最后改动 2026-11-01 17:35，此后无改动。

### 能力

四层并发（G 全局 / 组上限 min(limit,0.8G) / R 每资源 / S 每来源，界面四个滑杆且点数字可输精确值）、多任务组并行、来源池（一个资源 = 主 URL + `mirrors`，代理可写数组，展开成 URL×代理 的「来源」，开跑前每来源测速后按吞吐加权分片，多来源写 `<目标>.part` 校验通过才 rename）、hash 多算法强校验（`hash` 字典写几种验几种全过才算成功）、续传（分片级 + 远端身份校验 + `If-Range`）、多代理/单来源降级、界面玻璃卡片 + 分片切分条 + 来源行、CLI（`-no-gui` / `--task` / `--out` / `--g --r --p --s` / `--limit` / `--yes` / `--force-download|-fd` / `--wait` / `--help`，退出码 0/1/2/3）、把任务交给已运行实例（`second-instance` + `additionalData` + `--wait` 轮询结果文件）、内存任务（编辑器「直接开始下载」不落盘，组 id 记 `未保存任务#<内容哈希>`）。

### 构建与运行位置

原因见 20261101-003/004：构建输出必须给 `--config.directories.output=〈工作目录〉/adl/out`，成功后 robocopy 同步回 `adl\out\`；

运行/冒烟用 `〈工作目录〉/adl/out/win-unpacked/AD Downloader.exe`，**不要**从工作区里的 `out\` 跑。

### 产物

`adl\out\AD-Downloader-0.1.0-Setup.exe` 与 `〈工作目录〉/adl/out/` 同一份，106.5 MB，2026-11-01 17:39，未签名（首次运行会弹 SmartScreen）。

### 已知限制

无 BT/磁力/Metalink；不读写 aria2 的 `.aria2` 控制文件；多来源中某片来源中途挂掉整条资源失败（无改派）；主来源不可用但镜像可用也判失败；界面编辑器只能建单代理单 URL，多来源需手写 JSON。
