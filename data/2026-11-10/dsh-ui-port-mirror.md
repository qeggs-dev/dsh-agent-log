<!-- 20261110-007 -->

## 扫码页补上摄像头（站内扫码）

用户反馈「扫描页面没有打开摄像头的地方」，原来壳页只等系统相机带 `#t=` 进来。

现在 `shellPage()` 内置扫描器：`<video playsinline muted>` + canvas + 内置 `jsQR`（vendor，256 KB），**页面加载 400 ms 后自动 `getUserMedia({facingMode:'environment'})`**，另有「打开摄像头扫描」按钮与「停止」；

解出的文本用 `/[#&?]t=/` 取票据（也接受纯票据串），命中即停摄像头并走原来的 unlock 流程。`getUserMedia` 只在安全上下文可用，所以这个页面必须走 HTTPS（自签名接受后就满足）。

资产由 `/__mirror/assets/{sha256,jsqr}.js` 提供（`SHELL_ASSETS` 现在按 `['sha256.js','jsqr.js']` 循环读 vendor，未知名 404）。

### 验证

`verify-scanner.mjs` 检查页面含 `打开摄像头扫描`/`getUserMedia`/`jsQR`/`facingMode` 且两个资产 200；

`verify-qr.mjs` 用同一份 `qrcode.cjs` 生成矩阵、铺成 RGBA 后交给 **jsQR 解码，结果与原文完全一致**——证明设置页渲染的二维码能被站内扫描器读出。

### 注意

自动开摄像头会立刻弹权限框，桌面浏览器无摄像头时只会报错并提示改用「复制链接」。
