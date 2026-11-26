<!-- 20261126-012 -->

## 变形拼图 morph-puzzle 新建（2026-11-26）

用户提「HTML 小游戏，拼图，但拼图块会变形」，落成工作区 `morph-puzzle/`。

### 核心机制

棋盘每条内部切缝是一条解析曲线（窄高斯瓣，两端 window 收零），相邻格共用同一条曲线，所以任意时刻严格共边、缝隙本身在呼吸；

每块碎片另有一套「错位」参数，拖动时按 p = clamp((SYNC_RANGE - d)/(SYNC_RANGE - SNAP_DIST)) 从私有参数插值到棋盘当前参数——越靠近正确位置形状越吻合，形状本身就是冷热提示；振幅带符号，插值时凸起会缩平再从另一侧鼓出来（「翻过去」）。

已放置的格子先按这些格子的形状铺一层同图底、再画碎片，消除裁剪边透出深色底板的暗缝；拼好后切缝持续变形。

### 交付

`morph-puzzle.html` 单文件（78KB，双击即玩，tools/build-single.cjs 把 CSS/JS 内联生成）+ 开发版 index.html 与 src/（传统 script、file:// 可用）+ server.cjs 零依赖静态服务。

程序化生成六套配色画作、可上传照片换图、提示/预览/音效（WebAudio 合成、无音频文件）、桌面 4×4 与窄屏竖屏 3×3。测试 `node tests/run-all.cjs`（42 项全绿；`node --test` 会因沙箱 spawn EPERM，故用同进程 require 运行器）。

### 视觉验收路径

np 的 Playwright 与 loopback URL 都被拒，改用 np_load_page 的 file 加载单文件到 iframe 页面，再配 PMDebug.advance() 同步逐帧驱动（后台 iframe 的 rAF 会被节流，不能等真实时间）。
