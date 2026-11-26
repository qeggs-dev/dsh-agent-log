<!-- 20261022-002 -->

## 新增项目 **Requester** 于 `〈工作区〉/requ…

新增项目 **Requester** 于 `〈工作区〉/requester/`（TS，**Node 原生直跑 `.ts`、零依赖**，UI 尚未开始；M1 只交付引擎核心 + 44 项 `node --test` 用例全过）。

用户 2026-10-22 的定位演进是「Thunder Client 平替」→「发请求 / 记历史 / 分组 / 跑整组」→ 实际成型为**带任务注册表的 HTTP 编排引擎**（块模型与他的「带身份和注册表的 shell 作业控制」是同一套原语）。

### 模型

**组 = 根 `sequence`**；`sequence` 创建子作用域（块树 = 变量树），`parallel` **不建作用域**（分支共享变量、因此争锁）；

五种块 request / wait / variable(`set` 单键赋值、`lock` 出入锁壳带 children 临界区) / sequence / parallel。

退出信号 `ok | break(code) | cancelled | timeout | failed`，**`break` 是块级 return**（照 QQBot 的 `SubCmdBreaked`：上层只当返回值，`sequence` 默认**不**因非 ok 退出而中断，要停必须写 `stopOnError`；

「只跑某一块」靠只调那一块，与 break 无关）。变量锁粒度由用户 2026-10-22 拍板选 **A = 每作用域一把锁、锁壳只能锁当前作用域**（因此无 ABBA 顺序死锁），取锁超时默认 10s、超时判失败不挂死、排队态 `waiting-lock`。

任务管理器 = `runnings`/`results` 双表 + `forward`/`reverse` 正反索引（取消沿树走）；结果表保留最近 **20 次根运行**、淘汰时连子树一起清。

### 参考实现

`〈项目目录〉/QQBot/Nonebot/Repeater/Repeater/repeater/plugins/repeater_main/command_register`（`caller.py` 1805 行的 `CommandCaller` + `serial.py`/`parallel.py`/`cascade.py` 三个「控制流本身就是普通命令」的示范，比 `core/tool_caller` 那套成熟）；

### 两处有意偏离

①注册用工厂 `registerBlock({...})` 而不是 `@register` 装饰器——Node 原生执行 `.ts` 只支持可擦除语法，装饰器会让测试直接失败；②Node 单线程且注册表读写不跨 `await`，所以没有 Python 那套 `asyncio.Lock` 的对应物

<!-- 20261022-003 -->

## `node --test` 的默认隔离模式在「受限沙箱（workspace-write）」下必失败，在 danger-full-access 下正常

（同日两种模式都实测过，44 项用例：前者 `Error: spawn EPERM` errno -4048、一条用例都没跑；后者默认隔离 846ms 全过）。原因是默认隔离会给每个测试文件 spawn 子进程并走管道 stdio，受限令牌下起不了子进程。

### 与沙箱模式无关的写法是单进程

`node --test --test-isolation=none "test/*.test.ts"`（实测 610ms，更快），Requester 的 `npm test` 按此写死，两种模式下都能跑

<!-- 20261022-005 -->

## Requester 上抓到的真死锁（设计缺陷，已修）

变量锁壳持锁期间，壳里的 `variable set` 子块是**另一个 task id**，它再去 acquire 同一把作用域锁就会自己锁死自己——界面上表现为整组永久「运行中」、`run:done` 永不触发、响应面板空白（我第一版正是这么写的，单测里没有「锁壳内含变量块」的用例所以没抓到）。

### 修法

`BlockRuntime.lockHolder(scope)` 沿 `tasks.stackOf()` 找「执行链上有没有人已经持有这把锁」——临界区是**整棵子树**，不是单个 task；同时嵌套锁壳（同作用域）也按同一判据跳过取锁。变量写入另加默认 10s 等锁上限，宁可判失败也不许无声挂死。

### 回归用例两条

`锁壳里的变量写入不会把自己锁死`、`同一作用域里嵌套锁壳不会死锁`

<!-- 20261022-006 -->

## **本机 Electron 进程建不了 `%APPDATA%\R…

**本机 Electron 进程建不了 `%APPDATA%\Requester`（EPERM）——根因就是 `20261021-041` 那条：工作区整棵树带 `Mandatory Label\Low Mandatory Level`，而 Low IL 进程写不进 Medium 的 `%APPDATA%\Roaming`**（**我当天先判定为「原因未查明」，是错的**：我当时用 `Get-Acl` 查 mandatory label 得到空值，但 `Get-Acl` 的 Access 列表**不含完整性标签**，必须用 `icacls` 才看得到——`icacls` 对工作区根显示 `Mandatory Label\Low Mandatory Level:(OI)(CI)(NW)`、对 `node_modules\electron\dist\electron.exe` 显示 `(I)(NW)`；

同一次会话里 pwsh/node 能建是因为它们不是从 Low 目录启动的）。这与「渲染进程沙箱起不来」是**同一个根因**，所以也有同一个解：**把可执行文件放到正常目录（如 `〈第二工作区〉`）跑，就不需要 `--user-data-dir`、也不需要 `--no-sandbox`**。

结论性做法不变但定位要改：`main` 里用 `app.commandLine.getSwitchValue('user-data-dir')` 允许 Chromium 自带开关覆盖数据目录（**必须写在 `app.setPath('userData')` 之前并沿用该值**），本机从工作区直接跑时才带 `--user-data-dir=<工程>\.userdata`（已固化进 `launch.cmd`）；

打包产物在正常目录/正常机器上走默认 `%APPDATA%`、`sandbox: true` 也不受影响。另：`mkdirSync(USER_DATA)` 必须 try/catch，否则建不了目录时主进程在模块加载阶段就崩、窗口根本不出现

<!-- 20261022-007 -->

## Requester **请求级历史已交付并真机验收**（单测 6…

Requester **请求级历史已交付并真机验收**（单测 67 → **80 项全过**）。

### 落点

`src/main/history.ts`（不 import electron，可单测）+ `src/shared/mask.ts` + `src/shared/curl.ts` + 左栏「运行 / 历史」页签。

存储是 `<userData>/history.ndjson` 一行一条，**双上限 500 条 / 16 MB**（超字节时重写并砍到一半）、坏行跳过、单条响应体入库截 32 KB；

**列表走摘要、点开才 `history:get` 取全文**（避免每次刷新克隆十几 MB，agent 每次 task finish 都会触发刷新，已按 250ms 合并）。记录时机是**主进程订阅任务的 `finish` 事件**，引擎完全不知道历史存在；

`request` 块另外把「实发请求 + 未替换模板」写进 `task.detail`（前者可重发、后者保 `{{baseUrl}}` 可存回成块）。

### 实测

跑一组产生 3 条记录（POST /login、GET /echo?as=A、GET /echo?as=B），详情里 `authorization` 显示为 `Bearer demo••••（13 字符）`（打码只在展示层，文件仍是明文）；

「存为请求块」让块数 9→10 且新块 URL 是 `{{baseUrl}}/echo?as=B`（模板优先，占位符保住了）；「重发」产生新任务与新记录（ok · 12ms），不依赖当前变量值

<!-- 20261022-008 -->

## Requester 的 **Cookie 自动管理已实现并真机验…

Requester 的 **Cookie 自动管理已实现并真机验收**（单测 96 → **101 项全过**）。用户 2026-10-22 拍板的语义：①**每次运行开始时把整张 jar 压进快照栈**（栈深 = 运行次数，上限 20）；

②同名 cookie 被响应 `Set-Cookie` 覆盖时**服务器赢**，覆盖后 `source` 变 `response`；③「重置到上一个快照」= 弹栈并把 `source==='response'` 的条目恢复到快照值、`manual` 的一律不动。

### 实现

`src/core/cookies.ts`（解析/域名与路径匹配/`CookieJar`，不 import electron）+ `src/main/cookies.ts`（每组 jar + 快照栈 + `<userData>/cookies.json`）；

传输层逐跳收集 `Set-Cookie` 且**每条带来源 URL**（`HttpResult.setCookies: RawSetCookie[]`，重定向每一跳都算——只用最后一跳会丢掉 302 登录链路上的 cookie）；请求块显式写了 `Cookie` 头则**原样发、不与 jar 合并**；

域名/路径/secure/过期按浏览器官语义匹配但**不做 public suffix 列表**。

### 实测

`POST /login` 下发 `session=demo-session-1; Path=/` 与 `scope=api-only; Path=/api`，随后两次 `GET /echo` 只带 `session`（`/api` 那条被路径规则正确排除）。

### 踩到的真 bug

`setManual`/`reset`/`remove`/`clear` 只改 jar、没调 `syncFromJar`，导致 `cookies.json` 里落的是旧状态（界面上加了手动条目、重启后消失）——修法是这四个方法改完统一 `syncFromJar`，并用「落盘后重读」的单测锁住

<!-- 20261022-009 -->

## 用户对「单独的页面 + 2/3 屏幕」的原意是：Cookie 管理是主窗口内的整块切页、而 2/3 指的是主窗口尺寸

——我第一版做成了「新开一个 2/3 屏幕的 BrowserWindow」，被用户纠正（「我说主页面大点，没说新开窗口大点啊」）。

### 已改成

`#cookie-view` 作为 `.layout` 的第四块，切页时 `.layout.page-cookies { grid-template-columns: 236px 1fr }` 并隐藏中栏与右栏、左栏（组/运行/历史）保留；`cookies.html` 与 `cookies:open` 那条链路已删。

### 主窗口几何

`src/main/window-state.ts`：默认取所在显示器工作区的 **2/3 居中**，之后**记住上次拖出来的尺寸**（`<userData>/window-state.json`，`getNormalBounds()` + maximized 标志、400ms 合并写入）；

读回时与当前显示器交叉校验，露出不足 120px 就回退到默认值。

### 实测

全新启动 `outerWidth×outerHeight = 1707×933`（工作区 2560×1400 的 2/3）；写入 1100×760 后重启得到 `1100×760 @ (300,200)`，日志「窗口 1100×760（沿用上次尺寸）」

<!-- 20261022-010 -->

## Requester 已出 NSIS 安装包并真机验收

（`〈第二工作区〉/requester-out/Requester-0.1.0-Setup.exe`，106.40 MB，未签名 → SmartScreen 会拦）。

### 打包链路

`npm run dist` = make-icon → build.mjs → `electron-builder --win nsis`（electron-builder 26.15.3 + Electron 44.9.2，`electronDist: node_modules/electron/dist`）。

**新踩的坑（在 20261021-361 之外）**：`ELECTRON_BUILDER_CACHE` 也不能放工作区——从 `.cache` 里解出来的 `7za.exe` 是 Low IL，去打 Medium 的输出目录直接 `System ERROR: 拒绝访问`（`7za.exe a ... .7z` exit 2），所以**输出目录与 builder 缓存两处都要指到正常目录**（本机用 `DSH_Normal_Workspace\requester-out` 与 `...\requester-cache`）。

新增 `--smoke-check`：只 `existsSync` 检查 asar 内 `index.html/ui.js/style.css/preload.cjs`，打印 `SMOKE_OK`、退出码 0（实测 exit=0；

GUI 子系统 exe 必须用 `Start-Process -Wait -PassThru` 才拿得到退出码）。

**打包版验收（不加 `--no-sandbox`、不加 `--user-data-dir`，即别人机器上的真实姿态）**：4 个进程含 renderer（渲染沙箱正常）、`%APPDATA%\Requester` 自动创建（9.6 MB，含 cookies.json/window-state.json/logs）、窗口 1707×933（2560×1400 的 2/3）、`POST /login` 9.3ms 并抓到 `session`/`scope` 两条 cookie、快照栈深 3、历史 1 条——彻底印证了 20261021-041 的「根因是 Low 标签」结论

<!-- 20261022-011 -->

## Requester 按子代理的「本机特异性代码」审查修掉 5 条（审查结论

`src/` 里没有任何硬编码绝对路径/用户名/屏幕尺寸，问题都在别处）：①`webPreferences.sandbox` 由 `false` 改回 **`true`**（本机从工作区跑靠 `launch.cmd` 的 `--no-sandbox`，代码不留安全降级）；

②`toCurl()` 由 POSIX 单引号+`\` 续行改成**单行 + 双引号 + `\"` 转义**（cmd/PowerShell/bash 通吃，测试同步改），残留边界是正文含 `$`/反引号时 bash 会展开；

③`package.json` 加 `engines.node >= 22.18`（`--test-isolation` 与直接跑 `.ts` 都依赖新版）；

④`tools/ui-cookie-reset.js` 的 id 跟到现行 DOM（`cookie-add-*`/`btn-cookie-*`）并改成先点「Cookie」切页；⑤`tools/ui-cancel-check.js` 不再写死块 id `b8`，改为按 `badge === '等待'` 找块。

### 教训

验收脚本写死 DOM id 或示例工作区的块 id，改界面就会静默腐烂（表现只是截图 eval 报一句错）

<!-- 20261022-015 -->

## Requester 的请求编辑器最终形态：基础编辑在右栏侧边栏、底部「详情 ›」进整页页签

（用户 2026-10-22 三次纠正后定稿；单测 132 → **134 项全过**，安装包 23:24 / smoke exit 0）。

### 结构

点块树里的请求行**不跳页**，右栏侧边栏「编辑」页直接变成该请求的基础编辑（名称 / 方法 / Auth 摘要 / URL / 请求头列表 / 请求体列表），**「详情 ›」按钮放在侧边栏所有内容的最下面**，点了才进整页的六页签详情页（查询参数/请求头/Auth/请求体/重试/提取规则，左上「← 返回请求」回侧边栏）。

`state.page` 只有 `work | cookies | request-detail` 三个值（不再有整页的基础面板）。

两个位置共用同一套 `data-row-*` 委托与 `onReqFieldChange/onReqClick`（监听器同时挂在 `#tab-edit` 与 `#req-tab-body` 上），结构变化后由 `rerenderRequestEditor()` 按位置重绘；请求头名称列在侧边栏窄到 124px。

**连续踩的三个坑（都记在这里）**：①第一版把「基础面板 + 页签」压成一级整页（用户原话「先侧边栏有基础功能然后下面一个详情按钮」被我当初的 `ask_user_question` 选项吞掉了），②第二版又把基础面板做成整页（应该回到侧边栏），③第三版把用户那句「详情按钮在所有内容的下面」**误读成抱怨**、反手把按钮挪到页签行右侧——它其实是指令。

### 教训

**用户的纠错句可能是指令；「怎么还在 X」先复述现状确认，再改，不要反向改**。

### 技术面

`RequestSpec` 的 `params/headers` 为行数组（`{id, enabled, name, value}`）、`auth`/`body`(none|raw|form|multipart、FormRow 带 kind+filePath)/`retry`；

`compose.ts` 负责变量替换+参数追加（URL 有 query 就 & 接、没有就 ?、列表空不动）+Auth 注入（覆盖同名头）+四种 body 编码（multipart 读文件生成 boundary）；`retry.ts` 负责规范化与退避/抖动；请求块内重试并写 `detail.attempts`；

`detail.template` 存完整 RequestSpec（历史回存成块用它，二进制正文不支持重发）

<!-- 20261022-016 -->

## Requester 的运行默认改成「遇错就停」

（用户原话「还有默认不是应该先停下吗」，单测 132 → **134 项全过**，安装包重出 22:54 / smoke exit 0）。

### 改动

①`shell` 块（组根）新增 `stopOnError`，**默认 true**（`parseBlock` 用 `record.stopOnError !== false`，旧数据没写这个字段也按 true 走）；

`sequence` / `parallel` / `variable lock` 的默认值同样从「继续跑完」翻成「失败即停」。

②**语义收窄**：`stopOnError` 现在只在 `failed / timeout / cancelled` 时停，`break`（块级 return，用户之前定过）**永不停兄弟**——旧实现把它当"非 ok"，默认开启后会让一个主动退出的块把整组停掉。

新增 `isStopWorthy(exit)` 到 `core/types.ts`，四个壳统一用它。③界面：根节点编辑区新增「子块失败即停止（默认开启）」复选框，顺序组/并行组/锁壳的文案与默认勾选同步改成「默认开启」。

### 实测

演示服务停掉时跑整组 → **失败 · 28ms 立刻停住**（旧行为会继续把后面几个块全跑成失败）；服务起来后 → OK · 5186ms 跑完，cookie 正常带上。

### 注意这是行为约定的反转

以后再加壳类块，默认值都是「停」；要跑完必须显式 `stopOnError: false`

<!-- 20261022-017 -->

## Requester 加了 JSON 请求体编辑器（树形 + 源码双视图，Unicode / ANSI 只差转义）

（用户要「不手写、用 UI 和代码保证语法正确」，并要分开 `JSON - Unicode` 与 `JSON - ANSI`；单测 134 → **152 项全过**，安装包 23:48 / smoke exit 0）。

语义（用户选的口径）：**两种都按 UTF-8 发字节，区别只在文本形态**——Unicode = 非 ASCII 原样（`"名字": "张"`）；ANSI = 非 ASCII 一律写 `\uXXXX`（BMP 之外拆代理对，结果纯 ASCII，任何 charset 环境都不乱码）。

### 模型

`BodyMode` 增加 `json`；`BodySpec` 新增 `json: JsonNode`（真源）、`jsonEncoding`、`jsonView: tree|source`、`jsonSource`（源码视图暂存，只有语法合法才用于发送）；

`JsonNode = string|number|boolean|null|object{entries}|array{items}`，number 存**用户输入的原文**（大整数/小数不因往返变形）。

新模块 `src/core/json.ts`：`stringifyJsonNode(node, encoding, indent)`（自己写序列化，才能控制 ANSI 转义；

indent=0 走紧凑单行）、`parseJsonSource()`（取值用 `JSON.parse`，**定位用自带的递归下降扫描器**——V8 有些错误不带 position，只靠它给不出行列；扫描器给中文原因如「对象里多了个 }（是不是末尾多了逗号？

）」+ 行列号）、树操作 `getNodeAt/setNodeAt/addChildAt/deleteNodeAt/changeKind/uniqueKey/describePath`（路径是 `number[]` 下标序列，与键名含不含点无关）。

### compose

`mode=json` 时源码视图先解析、非法直接抛「请求体 JSON 源码有语法错误（第 L 行第 C 列）」，然后按 encoding 序列化，Content-Type 默认补 `application/json`；结构化数字非法时抛「「n」不是合法 JSON 数字」。

### store

`parseJsonNode` 递归校验、深度上限 64，`jsonEncoding/jsonView/jsonSource` 原样往返。界面（`renderBodyTab` 里）：结构化视图每行 `类型|键|值|✕`，对象/数组可继续嵌套、随时改类型，`＋ 字段/＋ 元素`；

源码视图 textarea + 实时校验，非法时**不许切回结构化、不许发送**；侧边栏只有 ~380px，`#tab-edit` 里把类型列压到 78px、键列 96px、值列允许收缩，否则会溢出被裁。

### 顺手修掉一个真 bug

侧边栏改造后 `data-req-url`/`data-req-method` 没有对应的 change 处理（旧监听器随页面删掉了），改 URL/方法其实**没保存**——验收脚本发出去还是老 `{{baseUrl}}/` 才暴露，已补在 `onReqFieldChange` 里。

### 端到端验证

树里建 `{"a":1,"名字":"张"}` → 选 ANSI → 运行 → `history.ndjson` 里实发正文是 `{\n  "a": 1,\n  "\u540d\u5b57": "\u5f20"\n}`，HTTP 200

<!-- 20261022-018 -->

## Requester 的「运行整组」改成跑「最外层分支」，不再无条件跑根节点

（用户原话：「运行整组不是运行根节点，而是当前选中节点往上找最靠近父节点的一层（如果自己上层就是根节点，那只运行自己）」；单测 152 → **156 项全过**，安装包 23:58 / smoke exit 0）。

### 规则

从选中块往上找**最靠近根节点的那一层**——选中的是一级子块 → 只跑它自己；选中的在更深处 → 跑它所在的那个一级分支（该分支里的所有子块）；选中的就是根节点、或压根没选中 → 整组。

### 实现

新增纯模块 `src/shared/blocks.ts`（`chainToBlock(root,id)` 给从根到目标的链、`topBranch(root,selectedId)` 给运行目标；

放在 shared 是为了能被 node --test 直接覆盖，`ui.ts` 带 DOM 测不了），`ui.ts` 的 `runGroup()` 改成 `topBranch()` 得到目标后决定走 `api.runGroup(groupId)`（目标是根）还是 `api.runBlock(groupId, blockId)`（目标是分支）；

`run:start` 两条路径在 main 里都走 `runBlockForGroup`，都会 push cookie 快照、注入组变量，所以行为一致，只是 label 变成「组名 / 块名」。按钮 tooltip 动态显示这次到底跑谁（「运行选中块所在的最外层分支：并发查询」/「运行整组（登录流程）」）。

实测（演示服务 + `history.ndjson` 增量）：选中一级子块「登录」→ 只产生 1 条 `POST /login`；选中并行组里的「查询 A」→ 产生 2 条 `GET /echo?as=A`/`as=B`（跑的是整个并行分支），没有登录；

选中根节点 → 4 条（登录 + 查询A + 查询B + 历史·查询B），耗时 5180ms（含 5s 等待块）说明整组才跑到等待块。顺带把 README 的块模型表补上「所有壳 `stopOnError` 默认 true」并新增「运行入口」对照表

<!-- 20261022-014 -->

## Requester 的界面文案过了一遍「专业化」审校

（由子代理执行，112 项测试仍全过、`node build.mjs` 通过）。

### 术语统一

`壳/组壳`→**根节点**（徽标、摘要、编辑器说明、删除提示全改；

`src/main/store.ts` 新增导出 `ROOT_NODE_NAME = '根节点'`，新建组/新工作区的根节点名就是它，旧工作区里「根节点名==组名」的旧默认也一并规范成「根节点」，用户改名过的保留）、`锁壳`→**变量锁/临界区**、`栈帧/帧/作用域`→**变量帧**、`取锁超时`→**获取锁超时**、`往里加块`→**添加子块**、cookie 快照的`栈深`→**快照深度**、`名字`→**名称**、正文里的 `cookie`→**Cookie**；

块类型徽标改成 `根节点/请求/等待/变量/顺序组/并行组`，窗口标题统一为 `Requester — HTTP 编排`。

### 子代理替我发现并被我修掉的两个真问题

①`ui.ts` 的 `addGroup()` 仍在造 `kind:'sequence', name:'根'` 并把根名设成组名（绕过 `ROOT_NODE_NAME`，重载前显示不一致）——已改成 `kind:'shell'` + `ROOT_NODE_NAME`（渲染进程不能 import 主进程的 store，否则会把 `node:fs` 拖进浏览器包，所以常量在 ui 层重复一份并注明必须与 store 一致）；

②`store.ts` 的校验错误文案仍写「必须是壳（shell）块」，会以 toast 出现——已改成「必须是根节点（shell）块」。

### 另外

根节点行原本重复三遍「根节点」，摘要改成 `N 个子块 · 顺序等待`；响应面板补一行「HTTP 4xx/5xx 记为请求成功」；徽标改名后同步更新了 `tools/ui-pkg-shell-check.js` 与 `tools/ui-shell-check.js`（按徽标文字定位，不同步会静默失效）

<!-- 20261022-013 -->

## Requester 打包已交付

（`〈第二工作区〉/requester-out/Requester-0.1.0-Setup.exe`，106.40 MB，未签名 → SmartScreen 会拦；`win-unpacked\Requester.exe --smoke-check` 打印 `SMOKE_OK` 且 exit 0）。

### 打包期新踩的坑

`ELECTRON_BUILDER_CACHE` 也不能放工作区——从 `.cache` 里解出来的 `7za.exe` 是 Low IL，去打 Medium 输出目录直接 `System ERROR: 拒绝访问`（`7za.exe a ... 7z` exit 2），**输出目录与 builder 缓存两处都必须指到正常目录**（本机 `DSH_Normal_Workspace\requester-out` 与 `...\requester-cache`）。

打包版验收（**不加 `--no-sandbox`、不加 `--user-data-dir`**，即别人机器上的真实姿态）：4 个进程含 renderer（沙箱正常）、`%APPDATA%\Requester` 自动创建、窗口 1707×933（2/3 工作区）、`POST /login` 9.3ms 且抓到 `session`/`scope` 两条 cookie、快照栈深 3。

打包配置写在 `package.json` 的 `build`（`electronDist: node_modules/electron/dist`、`files: dist/**` + package.json、`asar: true`、NSIS 非 oneClick）。

**注意 GUI 子系统 exe 必须用 `Start-Process -Wait -PassThru` 才拿得到退出码**
