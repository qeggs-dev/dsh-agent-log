<!-- 20261122-001 -->

## dsh-new-page 0.5.0（commit 21bb97…

dsh-new-page 0.5.0（commit 21bb979）新增「登录态 + 请求缓存」：页面里的 fetch/XHR 被桥接拦截，经父页面转发到 Host `POST /dsh-new-page/http`，由 Host 用 Node 直连目标站点（无 CORS）。

### 登录态

每个数据池一个 cookies/<pool>.json 罐，保存所有代理响应的 Set-Cookie（domain/path/expires/secure/httpOnly/sameSite，≤500 条），后续请求与 np_load_page/page navigate 的 HTML 抓取都带匹配 cookie；

页面自带的 cookie 头被忽略，document.cookie 仍是页面本地虚拟罐。

### 请求缓存

cache/<pool>/<sha256>.json，键 = pool+method+URL+cookie 头，遵守 no-store/max-age，ETag/Last-Modified 重新验证（304 刷新），网络错误退回 stale；单条 ≤4 MiB、单池 ≤64 MiB，最旧淘汰。

重定向改为手动逐跳，每一跳重新校验私网/回环（堵住 public→127.0.0.1 的 SSRF）。客户端 shim 支持 fetch 与 async XHR（text/json/arraybuffer/blob，事件/readyState），sync XHR/non-http 回退原生；

WebSocket/EventSource 不代理。设置页每个池显示「缓存 N 条 / X · 登录 Cookie M」并可清空缓存、清空登录 Cookie。

### 实机

Bilibili 页面内 fetch 与 XHR 调 nav 均 200（code:-101），二维码登录接口 code:0 有 qrcode_key；

经代理加载首页捕获 buvid3/b_nut（loginCookies 2），缓存 39–47 条/137 KiB，静态 JSON 第二次 fromCache true；清空后归零、重载恢复。

### 限制

未完成扫码，真实登录态未验证；IndexedDB/CacheStorage/SW 仍不可用；大于 12 MiB 的响应/媒体流不走代理；登录仍取决于站点 API 流程（UA/IP/验证码/WS）。

<!-- 20261122-003 -->

## dsh-new-page 0.6.0（commit 870c0e…

dsh-new-page 0.6.0（commit 870c0eb）新增 np_screenshot 工具与 capture.js：页面 iframe 是不透明源、父页面读不到像素，所以客户端只上报标签页矩形（页面 CSS px：left/top/width/height/dpr/clipped，通过 /events 的 rects 与 POST /rect 返回），Host 用 Koffi 绑 Win32 GDI 捕获整个 DSH 窗口（PrintWindow + PW_RENDERFULLCONTENT=2，失败或整帧全黑时退回窗口矩形 BitBlt），再按 ClientToScreen 得到的客户区原点换算、按 dpr 裁剪；

窗口级捕获无视遮挡，别的窗口盖住 DSH 也能截到页面。PNG 用 node:zlib 自写编码（不依赖 PowerShell）。

### fullPage

true 时先逐屏滚动探底（最多 12 屏）触发懒加载并量最终高度，然后在每次截图前隐藏 position:fixed/sticky 元素（防止固定头部重复），按 scrollTop×frameScale 拼进 RGBA 画布，结束后恢复原滚动位置与元素 visibility；上限 40 屏/3000 万像素。

### 实测

Bilibili 首页可见截图 913×1060 与标签页一致；fullPage 913×4230、5 屏拼接，懒加载内容完整、固定头部不再重复；结束后 scrollY 回 0、header visibility=visible。

### 限制

仅 Windows 桌面；标签页必须打开且可见；无限滚动信息流只截到本次量到的高度。

### 测试

host 20、proxy 15、env 15、pool 13 全绿。
