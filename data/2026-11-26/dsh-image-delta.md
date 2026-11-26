<!-- 20261126-001 -->

## image-delta（@local/image-delta v0.1.0）新建并安装

注册模型工具 `read_image_delta`，零 JS 依赖，只复用随 app.asar 打包的 `sharp`（解析链同 dsh-image-region）。输入两张**宽高必须完全一致**的图片（不一致直接报错并给出两边尺寸；**没有**九宫格对齐/缩放/补边——用户当场改口「我写错了，去除对齐方式，严格逐像素形状一致」），按 EXIF 摆正、转 sRGB、统一成 8 位 RGBA（缺 alpha 按不透明 255，直通 alpha 不预乘）逐像素取 `|a-b|`，写出：`red_delta.png`/`green_delta.png`/`blue_delta.png`（单通道灰度 PNG，colour type 0，亮度=|Δ|，0–255）、`alpha_delta.png`（仅当至少一方带 alpha 通道）、`total_delta.png`（RGB 三通道分别放三个 Δ 的绝对值，未变化处纯黑）。默认落 `<工作区>\screenshots\delta\<a 名>-vs-<b 名>\`，`out_dir` 可改但必须落在会话工作区内（只读会话直接报错）；返回绝对路径、不同像素数/占比（ratio + percent）、各通道 changed/max/mean，以及 `alphaCompared`。16 位输入先按 `v*255/65535` 归一到 8 位再比较。写文件用 `node:fs`（fs 接缝只有 writeText，没有字节写），写前按 `sandboxPolicy` 自限；并发安全，120s 超时。

**实测**（宿主内真实调用 + Electron-as-node 桩 harness 两条路）：120×90 RGBA 图 4 个已知差异 → 4/10800 = 0.04%，red max 229 / green 50 / blue 25 / alpha 120，输出 PNG 逐像素核对（red(10,10)=100、(13,10)=229，green(11,10)=50，blue=25，alpha=120，total(13,10)=229,0,0）；RGB 对只出 4 张图、无 alpha_delta；尺寸不一致被拒（`image_a is 120x90 px but image_b is 60x90 px`）；灰度 L 图与同值 RGB 图比较 0 差异（`.toColourspace('srgb')` 对 b-w 是恒等）；16 位对 2 个差异 max 15。

**踩坑**：第一次装的版本把灰度图编码成 RGB（`sharp(raw 1ch).png()` 默认按 sRGB 输出，Pillow 读出来 mode=RGB、字节数 145 而非 120），修正为 `.toColourspace('b-w')`；**已安装（link:）插件的 index.js 改动不会热加载**，必须 `restart_dsh` 才生效——重启后真实工具调用才输出 colour type 0 的 120 字节文件。仓库 `dsh_plugins/image-delta`（git 两次提交 `0af5e34` feat、`88b5fd5` fix，main 分支）；`package.json` 导出 locale/icon、`files` 已列全；README 写清了语义/限制/安装卸载。**未验证**：插件管理里图标与中英文文案的实际渲染（无页面级检查）。
