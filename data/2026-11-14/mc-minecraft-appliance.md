<!-- 20261114-029 -->

## MC 裸机项目（用户 2026-11-14 拍板）

目标是「极小内核 + 全部资源只服务 Minecraft」的 appliance（主机式），不是通用 OS，也不是单纯把 JVM 弄上裸机。

### 范围裁剪

只做原版 MC、不加模组、不需要模组支持；工作量最小优先。起步版本锁 1.12.2（GL 2.1 固定管线、Java 8、LWJGL 2.9.4），后续再逐版本加；

### 版本-图形门槛

1.16.5 及以下 GL 2.1，1.17–1.21.8 需 GL 3.2 core，1.21.9+ 需 3.3。

### 实现路线

M1 先用自己的 launcher 在宿主/Linux 跑通并量基线（加电到主菜单秒数、帧率、RSS）；M2 换微内核 + personality 层（只实现 HotSpot 实测出的 syscall 子集，约 60–100 个）；M3 客户端 GL 栈（软件光栅化，目标 720p/30fps）。

已知不可删的硬依赖：真线程（渲染/区块构建/GC/JIT）、2–4GB 堆、GL 栈、键鼠输入；音频可先静音。产物在 〈工作区〉/mc-baremetal/（tools/fetch-mc.mjs 拉取布局、tools/run-mc.mjs 离线启动），JDK8 取自清华 Adoptium 镜像。

<!-- 20261114-030 -->

## MC 裸机 M1 基线（2026-11-14 实测，Windows 宿主）

原版 1.12.2 客户端 + 自写离线 launcher 已跑通，不依赖官方启动器与账号。

工具在 `〈工作区〉/mc-baremetal/`：`tools/fetch-mc.mjs`（拉 version.json / client.jar / libraries / natives / assets 并生成 layout.json，~150MB 约 40 秒）、`tools/run-mc.mjs`（读 layout.json 组命令行离线启动，MC_USER/MC_MEM/MC_JAVA/MC_GAMEDIR 可覆盖）。

### 关键环境事实

① JDK8 必须用 Temurin 8u512，从清华 Adoptium 镜像直下（106MB/4s，`https://mirrors.tuna.tsinghua.edu.cn/Adoptium/8/jdk/x64/windows/OpenJDK8U-jdk_x64_windows_hotspot_8u512b09.zip`）——本机只有 JDK 17/18/19/21，没有 8；

② 沙箱禁止管道 stdio，node 里 `execFile` 解压 natives 会 spawn EPERM，改 `spawnSync(...,{stdio:'ignore'})` 才行；③ 本机 `tar`（bsdtar）不支持 7z 的 LZMA，解 mesa-dist-win 要用 `〈本机路径〉`；

④ MC 1.12.2 用 LWJGL 2.9.4（不是 LWJGL 3），natives 是 lwjgl/jinput/text2speech 三个 jar；

⑤ Windows 上用 Mesa 软件渲染：把 `opengl32.dll`+`libgallium_wgl.dll` 放进 jdk8 的 bin 目录即可，配 `GALLIUM_DRIVER=llvmpipe`、`LIBGL_ALWAYS_SOFTWARE=1`，`GALLIUM_HUD=fps` 能在画面左上角直接显示帧率（不需要 F3）。

### 基线数字

冷启到主菜单约 24 秒；llvmpipe 856×512 主菜单 **29.97 FPS**；llvmpipe 进程 RSS 约 838MB。菜单帧率不代表世界内帧率，下一步要用预生成存档量世界内。
