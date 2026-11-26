<!-- 20261125-010 -->

## dsh-new-page 0.8.0（commit 46dbef…

dsh-new-page 0.8.0（commit 46dbefa）给 np_create_page 加 renderer 枚举：iframe（默认）或 electron_webview。

webview 页用 DSH 桌面预加载的 window.dshDesktop.browser.acquire(workspaceKey)（key=dsh-new-page:<pool|pageId>）拿主进程 guest lease + 进程级 session 分区（dsh-sidebar-browser-<uuid>，无 persist:，重启即清），创建 <webview name=lease partition=… src=about:blank#lease allowpopups>；

主进程 will-attach-webview 加固 nodeIntegration/contextIsolation/sandbox/webviewTag。内容只接受 URL：np_load_page 对 webview 页只收 url、Host 不抓取（bytes:0），客户端 loadURL；

np_exec 走 webview.executeJavaScript（无 console 捕获、无顶层 await）；

np_screenshot 走 webview.capturePage（toPNG 在本渲染器不能分配 Buffer，改用 NativeImage.toDataURL 取 base64，POST /snapshot，Host mode=webview）。

### 关键坑

webview 放在 block/absolute 容器里 guest 视口恒为 300×150；

必须像内置侧栏浏览器那样作为 flex 子元素（display:flex;flex:1 1 auto;min-width/height:0;width/height:100%），且不要用 nudge/ResizeObserver 反复改尺寸——那会造成页面持续闪烁；

等待标签页达到真实尺寸再创建（height≥300），之后交给 flex。实测 example.com：guest inner 913×1060、np_exec 返回 title/URL、np_screenshot 913×1060 mode=webview。

测试 host 21 / proxy 15 / env 15 / pool 13 全绿。

<!-- 20261125-011 -->

## dsh-new-page 0.8.1（commit d4ba6f…

dsh-new-page 0.8.1（commit d4ba6f3）把 renderer=electron_webview 从自绘 webview 改为直接复用 DSH 官方 Sidebar Browser：客户端 ensureOpen 检测到 webview 页就调 ctx.sidebarRight.openTab("browser", {params:{url}})，后台会话用 openTabIn；

先在 tabsIn 里按 url 找已开的 browser tab，避免重复。插件不再创建 <webview>，自绘版的尺寸 300×150/闪烁问题随之移除（此前用 flex 子元素布局能修尺寸，但 nudge/RO 仍会闪）。

### 工具

np_exec 通过 document.querySelectorAll("webview[data-sidebar-browser-frame]") 按 url 精确匹配（否则取可见的）定位官方 guest，必要时先触发打开再轮询等待挂载，然后 executeJavaScript；

np_screenshot 同样定位后 capturePage，NativeImage.toDataURL 取 base64 发 /snapshot，Host mode=webview。官方标签页的存储是进程级分区（无 persist:），DSH 重启清空；

webview 页只接受 url（Host 不抓取，bytes:0）。

### 实测

建页后 ensureOpen.browserOpened，自绘 webview 数量 0；example.com 官方 guest 913×1022，np_exec 返回 title/URL，np_screenshot 913×1022。

测试 host 21 / proxy 15 / env 15 / pool 13 全绿。

<!-- 20261125-012 -->

## dsh-new-page 0.9.0（commit 9c6e6c…

dsh-new-page 0.9.0（commit 9c6e6c0）新增 renderer=playwright（后台自动化，无实时画面）：np_create_page 的 playwright 参数 executablePath/channel/headless(默认 true)/userDataDir/args 存 PageMeta；

np_load_page 对 playwright 页只收 url（Host 不抓取，bytes 0）；np_exec 用 Python Playwright CDP Runtime.evaluate（awaitPromise+returnByValue）；

np_screenshot 用 page.screenshot({fullPage}) 原生整页，mode=playwright。

### 实现是一次性会话

pwRun 写 args JSON，经 ctx.shell 执行 `& <python> pw_helper.py <args>`（会话 danger-full-access），helper 在 import playwright 前把 TEMP/TMP/TMPDIR 指向会话工作区 .dsh-new-page/pw-temp，启动浏览器→导航→动作→关闭，stdout 一行 JSON，Host 解析。

### 关键坑

Host 裸 spawn 的 Python 子进程被沙箱化，没有可写临时目录（Playwright 报 No usable temporary directory / mkdtemp EPERM 到 plugin-data），且 Playwright 驱动 mkdtemp 在插件数据目录 EPERM；

改走 ctx.shell + 工作区临时目录后正常。

### 实测

executablePath 指向系统 Edge、headless、args 生效；example.com np_exec 返回 title/url/1280×800（约 13 秒）；fullPage 截图 1280×800、mode=playwright。

### 限制

每次调用重启浏览器（约 5-13 秒），无 userDataDir 时 cookie 不跨调用；需要本机 Python+Playwright（配置 playwrightPython / DSH_NEW_PAGE_PYTHON，默认自动探测工作区 .venv）；playwrightTimeoutMs 默认 30s。

测试 host 22 / proxy 15 / env 15 / pool 13 全绿。
