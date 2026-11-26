<!-- 20261030-001 -->

## 新插件「JS 库缓存」

（`〈工作区〉/dsh-lib-cache`，包 `@local/dsh-lib-cache` v0.1.0，desktop profile bundle，entry `include:lib-cache`，`application: applied`、`fiberPhase: active`）：用户三次收窄后的最终形态——**不注册工具、不做 UI，只提供插件接口**，语义是「**传入 url 和 id，返回可直接 import 的库文件**」。

Host 服务 `libCache`：`fetch(url, id, {version})` 下载并缓存、返回 `{id, version, file, bytes, sha256, contentType, source, etag, path, route, url}`；

`import(id, version)` 在 Host 进程内直接 `import()`；另有 `refresh/get/versions/list/file/read/text/url/route/remove/prune/stats`。

Client 半提供同名服务：`import(id)` / `url(id)` / `script(id)`（UMD）/ `text(id)` / `list/available/refresh`，只读 `/lib-cache/index.json`、不联网。

### 版本规则

省略 `version` 时版本＝内容 sha256 前 12 位（同字节不新增、变字节必新增），`refresh` 带 `ETag`/`If-Modified-Since`（304 不新增版本），`latest` 由写入推进；显式 `version` 是可变标签，同标签再刷新会被新内容覆盖。

布局 `<cacheDir>/index.json` + `files/<id>/<version>/<file>`，cacheDir 默认 `$DSH_HOME/plugin-data/dsh-lib-cache`。

### HTTP

`GET /lib-cache/<id>/<version>/<file>`（`text/javascript` + `immutable` + `ACAO:*` + `ETag`）与 `GET /lib-cache/index.json`。

### 两条实测的运行时事实

①`webServer.register({kind:'prefix'})` 的匹配是 `pathname === path || pathname.startsWith(path + "/")`（读 `dsh-host-webserver/lib/index.js` 确认），所以**注册路径不能带尾斜杠**——第一版注册 `/lib-cache/` 导致线上永远 404，而插件 fiber 仍显示 `active`（父 fiber 活跃 ≠ 注入子 fiber 成功），极易误判「插件没生效」；

②`install_bundle` 第一次报 `EPERM ... rename package.json.<rand> -> package.json`（pnpm 写 profile 的 package.json），**原样重试一次即 applied**，package.json 无半成品残留。

### 验证

`tests/store.test.mjs` 6/6（本地 HTTP 源、内容哈希版本、refresh/304、错误分支、prune/remove/stats、路径逃逸）、`tests/host.test.mjs` 1/1（真 Cordis 上下文 + 另一插件 `inject:['libCache']` 消费 + Host 侧 import ESM/CJS + 路由 200/304/HEAD/404/405）、线上 `/lib-cache/index.json` 返回 200。

### 未验证

Client 半的真实加载——新增 `dsh.client` 声明要重载一次 App 才进 boot graph；直连 `/plugins/<id>/client.js` 对已加载的老插件也 404（怀疑缺 `?rev=`），该探测方式无效。

<!-- 20261030-002 -->

## 新插件「Mermaid 渲染」

（`〈工作区〉/dsh-mermaid`，包 `@local/dsh-mermaid` v0.1.0，desktop profile bundle，行 id `mermaid`）：Host 半把 mermaid **12.2.0** 的浏览器构建 `dist/mermaid.min.js`（**5,494,801 B**，sha256 `a8a6a6f8…`，单文件、末尾 `globalThis["mermaid"]=…`，无相对 import）预下载进 dsh-lib-cache（id `mermaid`），再注册 `POST /mermaid/report` 与 `GET /mermaid/state`；

Client 半用 `ctx.get('libCache').script('mermaid')` 载入后渲染图表。

**本机 jsDelivr 连不上（`ECONNRESET`），unpkg 正常**，故默认源是 `https://unpkg.com/mermaid@{version}/dist/mermaid.min.js`。

<!-- 20261030-005 -->

## dsh-mermaid 的形态与验收方式

显示策略是**源码与图都保留**、中间一条 `--dsw-alias-border-l1` 细分隔线（用户 2026-10-30 明确要求，不要隐藏代码）；启发式命中的块解析失败时**静默**（只有显式 mermaid 标记才报错行）。

因为本机没有浏览器控制，插件内置诊断：Client 每次扫描（≤4 s 节流）把快照 POST 到 `/mermaid/report`，Host 写 `<DSH_TEMP_ROOT>\dsh-mermaid\report.json`（字段：`library`、`counts{blocks,rendered,surfaces,pendingFailures}`、`stats{attempts,settled,timedOut}`、`selfTest{outcome,ms}`、`lastError`、`samples[]` 含 `label/explicit/preClass/children/state`）。

### 实测读数

`selfTest:{outcome:"ok",ms≈560}`、`rendered:1`、`surfaces:1`、`stylesApi:"absent"`；用户截图确认渲染成功。**改动 Client 半必须重启 App**（模块被缓存），Host 半同理。

<!-- 20261030-007 -->

## dsh-mermaid 已加缩放/平移

（替代 006 的待办）：图区上方有 `−` / 百分比 / `+` 三个控件，百分比按钮＝恢复适应宽度。

**实现不用 `transform: scale()`**，而是从 `svg.viewBox.baseVal` 取自然宽度，按视口宽度算 `min(自然宽, 可用宽) × zoom` 写成**显式像素宽度**（同时 `removeAttribute('width'/'height')`、`style.maxWidth='none'`，因为 mermaid 会写 `width="100%"` 与内联 `max-width`），溢出交给 viewport 的原生滚动条 ⇒ 图保持矢量、不糊。

范围 40%–400%，`+`/`−` 步进 1.25×、**滚轮直接缩放 1.12×（Ctrl+滚轮更细 1.08×）**——用户 2026-10-30 明确选定「悬停即滚轮缩放」，代价是图区上不再滚页面、要滚页面得把指针移出图区；放大后指针拖动改 `scrollLeft/scrollTop`，双击或点百分比复位；

高度超 620px 时 viewport 内滚动。**缩放按源码哈希存 `state.zoom`**，主题切换 / Chat 行卸载重挂后保持。

### 细节

`canvas` 用 `width:max-content + min-width:100% + flex 居中` 让小于容器宽度时居中；

尺寸重算走 `state.appliers`（每张图一条 `{viewport, apply, observer}`，`ResizeObserver` + 窗口 resize + `requestAnimationFrame` 各一次），`scan()` 里 `sweepAppliers()` 清掉已卸载行的条目、`cleanup()` 里统一 disconnect。

### 验收

`node --check` 通过；重启后 `report.json` 为 `rendered:1 / surfaces:1 / lastError:null`（`mountDiagram` 抛错会走 `fail()` 写 lastError，为 null 即说明工具条与 viewport 建起来了）；

滚轮/拖动的手感仍需人眼确认。
