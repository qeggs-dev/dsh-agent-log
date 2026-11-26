<!-- 20261121-002 -->

## 新增 DSH 插件 @local/dsh-new-page（工作…

新增 DSH 插件 @local/dsh-new-page（工作区 dsh_plugins/dsh-new-page，独立 git 仓库，已 install_bundle 装入 desktop profile）。

### 三个工具

np_create_page 建一个带 id（np-1、np-2…）的空白页并让右侧栏打开它的标签页；np_load_page 用 content/file/url 三者之一替换指定页面内容（url 由 Host 抓取、20s 超时、按 content-type 只收 HTML/SVG/纯文本，纯文本包 <pre>）；

np_exec 在必填 page 指定的页面 iframe 里求值 JS，回传 value/valueType/logs/error/durationMs。

页面是右侧栏的 multiple+keepMounted tab：body 用 sandbox iframe（无 allow-same-origin），bridge 由客户端注入 srcdoc、postMessage 执行，所以页面没有 localStorage/cookie、碰不到 DSH 页面。

设置页「自定义标签页」有开关「自定义标签页操作需要审批」（写 $DSH_HOME/plugin-data/dsh-new-page/settings.json，默认关；按 R-035 先看会话权限，danger-full-access 不弹审批）。

### 关键设计

①tab 地址 sidebar://new-page/<uuid> 在页面 mount 时 POST /bind 持久化，关标签页与刷新都不清，否则刷新后恢复的标签页找不到页面；

②np_exec 任务走长轮询并采用 offer+claim（/claim 1.2s 内确认否则重新发放），只有最新 /hello 的 clientId 能领取，避免刷新时旧页面那条已死的轮询把任务吞掉；

③np_exec 在页面已挂载时静默执行：不抢焦点、不展开侧栏、不重载（用户 2026-11-21 原话「np_exec 应该是只执行子页面」）；④页面运行时状态不持久，刷新/重启只剩源 HTML；⑤页面 id 显示在标签标题后面。

### 验证

Host 单测 15 项全绿；实机验证 content/file/url 三来源、value/logs/error 分支、刷新与重启后标签恢复、侧栏收起时静默执行、两页面状态隔离、设置页开关持久化；审批卡未实测（会话为完全访问权限）。

<!-- 20261121-003 -->

## dsh-new-page 0.2.0 追加数据池（commit 7a84cf4）

用户 2026-11-21 要求：创建页面时指定数据池名称；设置页可管理；不指定池的页面不允许加载内容；池「包含但不限于」cookie/localStorage。

### 实现

PageMeta.pool；pools/<name>.json = {version,name,areas:{区域名:JSON},updatedAt}，areas 是开放式区域映射（现实现 localStorage/cookies，未知区域原样保存，sessionStorage 永不落盘）；

页面脚本通过 window.__NP_POOL_SEED__ 拿到 localStorage/document.cookie/sessionStorage 的 shim，写入以 ops 操作批次 POST /pool（不是整份快照），Host 合并后返回 areas——整份快照会让同名池的后写者抹掉前者的键，ops 才支持共享。

设置页列出池（页面数、区域键数、字节）、清空（清空后 bump epoch 让绑定页面从空池重载，旧文档按 epoch 丢弃迟到写入）、删除（仍有页面引用时禁用/409）。

### 路由

GET/POST /pool、/pool/clear、/pool/delete；state.pools；np_create_page / np_load_page 增加 pool；np_exec 对无池页面直接报错。

### 限制

整池 ≤1 MiB、≤16 区域、扁平区 ≤500 键、cookies ≤200、键/值 ≤64 KiB。

### 验证

Host 单测 16+13 全绿；实机验证带池页面、localStorage/cookie 跨刷新、同名池共享且 A/B 键都保留、无池页面拒绝加载/执行、设置页池列表与清空；审批卡仍未实测（会话为完全访问）。

池里另有两点刻意设计：cookie/localStorage 是插件虚拟 shim（不透明源，页面的网络请求不带 cookie）；页面之间的内存视图不互相同步，只有重新加载页面才吃到对方写入。

<!-- 20261121-004 -->

## dsh-new-page 0.2.1（commit 见 git…

dsh-new-page 0.2.1（commit 见 git log）在设置页为每个页面加了「关闭页面」（用户 2026-11-21 要求「应该可以在设置栏里关闭页面」）。

### 行为

两步确认（首次点击按钮变「确认关闭」，3 秒内再点才执行，避免误删）；

关闭时先关掉该页在右侧栏的所有标签（按 tabIds 与已保存的 tab 地址绑定查找），再 POST /dsh-new-page/page/close，由 Host 从 pages.json 移除、删除 pages/<id>.html、把 activePageId 切到幸存页面（没有则 null）、bump revision；

未知 id 404。数据池不连带删除，等没有页面引用后可在池列表删除。UI 不引入新工具（仍是三个工具），关闭只走设置页。

### 验证

Host 单测 17 项（新增关闭页面用例）+ 数据池 13 项全绿；实机两步关闭 np-6 后标签消失、页面列表与磁盘删除、内容路由 404、活动页切到 np-8。

<!-- 20261121-006 -->

## dsh-new-page 0.3.0（commit 17a7c4…

dsh-new-page 0.3.0（commit 17a7c44）新增「页面环境」：建页时可指定 width/height（200–4096，必须成对）、userAgent（字面 ≤1024 或预设 desktop/mobile/tablet，建页时展开成具体 UA 字符串存储）、language（BCP47 形状 ≤35）、platform（≤64）、touch（布尔）、deviceScaleFactor（1–4）；

PageMeta.env 七字段全部有默认值（null/false），旧页面加载时 sanitize 补默认；np_load_page 明确不改环境（要换环境只能新建页面）。

客户端把 env 预置为 window.__NP_ENV__，桥接脚本在页面脚本前遮蔽 navigator.userAgent/appVersion/platform/language/languages/maxTouchPoints、window.devicePixelRatio/ontouchstart、screen.width/height/availWidth/availHeight 与 outerWidth/outerHeight；

固定视口用真实 390×844 布局（不是缩放伪造），页面按 min(1, 可用尺寸/视口) 缩放居中，带「390×844 · 100%」徽标，媒体查询按指定分辨率生效。设置页页面行显示环境摘要（尺寸/UA/touch/DPR）。

### 验证

Host 单测 15（env）+17（host）+13（pool）全绿；

实机 390×844+iPhone UA+zh-CN+iPhone 平台+touch+DPR3 页面读出 innerWidth/Height=390/844、screen 同尺寸、UA/语言/平台/触摸点/DPR 全对、@media (max-width:500px) 生效。

### 限制

UA 预设是固定字符串；时区与 Intl 区域格式不能按页面改；环境建页时固定。

<!-- 20261121-007 -->

## dsh-new-page 0.3.1（commit 见 git…

dsh-new-page 0.3.1（commit 见 git log）修正标签页的会话定向（用户 2026-11-21 要求：「设置中的打开标签页应该是在执行它的会话里打开；创建也是应该在执行它的会话创建」）。

### Host

create/load 的 focus 事件新增 focusSessionId（取 exec.agent.session.id），/state 与长轮询都带；

### 客户端

pollLoop 读 focusSessionId，ensureOpen 增加 sessionId 参数——目标会话在前台就正常打开/聚焦，在后台就调 openTabIn 在它的右侧栏开好且不切当前视图；

打开失败（目标会话的 store 尚未挂载）写入 pendingOpens 并用 400ms 重试泵反复尝试，直到挂上；mounted 变化时重试。设置页「打开标签页」显式传 bridge.currentSessionId()（=打开设置页所在会话），不再隐式落到碰巧可见的会话。

客户端重载后会用 focusPageId+focusSessionId 补开一次（focusAttempted 去重，用户手动关掉后不会反复打开）。

### 验证

Host 18 项单测（新增 focusSessionId 用例）+ env 15 + pool 13 全绿；

### 实机

当前会话创建页 → ensureOpen.open 带本会话 id；设置页打开工作台 → 落在本会话；会话 B 用 session_create 调 np_create_page → state.focusSessionId=B，会话 A 的可见右侧栏没有该标签，切到 B 后标签存在，重载后 B 的标签自动补开。

注意右侧栏会同时渲染多个会话的面板（背景会话 width=0），判断可见面板要看 width>0/可见性，不能取第一个 [data-sidebar-right-session]。
