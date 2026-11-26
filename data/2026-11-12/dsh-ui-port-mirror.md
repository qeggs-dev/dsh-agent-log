<!-- 20261112-016 -->

## 侧边栏开关悬停出二维码（**停留 1 秒**才弹，防误触）

镜像「已开启且暴露到局域网」时，鼠标在 sidebar.footer.action 的开关上停留 1000 ms 后才创建浮层；提前移开（加 onBlur / 卸载）会 clearTimeout 并移除，所以贴着边划过去不会生成票据。浮层是命令式的——DOM 建 div[data-uipm-qr-pop] 追加到 document.body（position:fixed，按 buttonRef 的 getBoundingClientRect 算 left / bottom），避免侧边栏 overflow / transform 裁切；图片地址带 ?v=<时间戳>，每次弹出取 currentTicket（120 s 内复用同一张票，不是每次新建）；文案「扫码在手机上打开」。未开启或未暴露（host 回环）时不弹。实测 verify-client.mjs：bundle 含 qrHoverTitle 与 data-uipm-qr-pop。
