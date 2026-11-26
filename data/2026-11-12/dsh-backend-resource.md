<!-- 20261112-006 -->

## 新增插件 **`@local/backend-resource`…

新增插件 **`@local/backend-resource`**（工作区 `〈工作区〉/backend-resource/`，v1.0.0，bundle 行 id `backend-resource` / entry `include:backend-resource`，`install_bundle` 以本地目录装入 desktop profile → `application: applied`、warnings 空）：用户要求「像 DSH 后台任务那样管理后台资源，并提供与后台任务一样的可关闭 UI，提供插件接口可以注册任何 JS 对象并注册取消回调」。

### Host 半

`registry.js` 纯逻辑 + `index.js` 接线：`ctx.provide('backendResources', …)`（**普通对象，不是 Service 类**，消费方 `inject: ['backendResources']` 即可）；

API = `register({ value, label, kind?, detail?, sessionId?, cancel? }) → handle { id, value, status, error, cancel(reason), release(), dispose() }`、`list({ sessionId? })`（全局资源 + 该会话资源，视图**永不含 value**）、`get/has/entries/cancel/release/cancelAll/onChange/size/revision`。

### 语义

`active → cancelling → cancelled`，取消回调抛错 ⇒ `failed`（记录保留、错误可见、可重试）；取消进行中再请求只返回 `cancelling`（**回调绝不重入**）；`release()` 只摘记录不调回调；

插件卸载 ⇒ `dispose` 全部（`unloadTimeoutMs` 默认 3000，超时后仍挂着的记录被强制摘下）。

### Client 半

`client.js`，纯 JS + React：slot `conversation.session.header.actions`（id `backend-resource`、order **30**，排在 shipped `job-list` 之后），**有资源才出现**；

chip 计数 + 可关闭面板（点面板外 / Esc / 滚动 / 右上角 × 都关），行内「关闭」，失败行「重试 / 移除」，关闭中显示「关闭中」；

浮层 **portal 到 document.body**（会话标题栏有 overflow:clip + mask，原地渲染会被裁——与 `id:20261106-004` 同一个坑），样式只用 `--dsw-alias-*` token。

### HTTP

`GET /backend-resource/state?session=`（同源可读，返回 `{ok,token,revision,resources}`）与 `POST /backend-resource/cancel`（`{id}` / `{id,release:true}` / `{all:true,reason}`；

要求 token 头 `x-dsh-backend-resource` + 同源），实测 200 / 403（无 token、跨源）/ 404（未知 id）/ 405（方法错）分支齐全。

### 配置

只有 `unloadTimeoutMs`；

**注册表默认空、不带任何内置资源**——最初为了「一装上就能看到界面」内置过一个 5 秒跳动的示例资源，用户确认空态行为无误后已将其从 `index.js`、`cordis.patch.yml`、README 里全部删除（删改后需重启才从源码层面生效，运行中的实例是先用 `POST /backend-resource/cancel` 把那个 `demo-1` 关掉、当场得到空表的）。

### 验证

`tests/registry.test.mjs` **14/14 全绿**（命令 `node --test --test-isolation=none "tests/*.test.mjs"`，沙箱里裸 `node --test` 会 spawn EPERM）；

线上用临时包 `@local/probe-resource`（`inject=['backendResources']` + `ctx.effect(() => handle.dispose)`）实测跨插件注册成功（出现 `probe-2`），把该行关掉后资源立即从列表消失、`Config.listConfigs` 回空，随后 `remove_bundle` 清干净——即「任意 JS 值 + 取消回调」与「卸载即回收」两条契约都端到端成立；

关/开本插件行同样热生效（关后路由 404，UI 不刷新页面就自己恢复）。

### 空态已实测

关掉最后一个资源后 `state` 回 `[]`、`{all:true}` 得 `cancelled:0`、未知 id 得 404、chip 在一个轮询周期内消失且页面无异常，重新登记后 chip 自动回来。

### 配色修过一次

初版面板底色用 `--dsw-alias-bg-overlay`（浅色 `#E9ECF2`、深色 `#61666B`，两种主题下都偏灰）所以看起来「没跟随深浅色」，已改用宿主菜单材质 `--dsw-specific-menu` + `--dsw-menu-backdrop-filter` + `--dsw-elevation-prominent` + `data-menu-material`（运行版 `ui-jobs` 的 `client.js` 里 `.menu` 即此配方）；

该版只跑过重启，**面板配色尚未经人眼/截图复核**。

### 滚动关面板的缺陷已修

面板原来在任意 document scroll 时关闭（为了不脱锚），而会话每加一行工具卡片、每流一个 token 都在滚动，于是用户看到的是「每一轮调用都自动消失」；

现在 scroll/resize 用 rAF 重新锚定到 chip（盒子没变就不重渲染），只有 chip 本身滚出视口才关，并补了「最后一个资源消失时先 setOpen(false)」避免之后误弹开。

### 另加可变元数据 API

`update(id, patch)` 与 `touch(id, at?)`（handle 同名方法；

`label`/`detail`/`startedAt` 可改，`detail: null` 清空，未知 id 抛 `unknown-resource`，已关闭的 handle 返回 `false` 不抛），用来让生产方刷新 UI 上的「已存活时长」；测试加到 **17 项**。

### 限制

改 `index.js` 仍须重启 App 才载入新模块（与 `id:20261112-003` 一致），改 `client.js` 刷新页面即可。

![backend-resource 实机截图：会话标题右侧的「1 个资源」chip 与展开后的可关闭面板（标题/计数/× 关闭、`demo 示例资源` 行 + 「关闭」按钮、注册提示行）](backend-resource-panel-20261112.png)

![backend-resource 实机截图（插件关→开后）：面板仍在原位并重新显示被重新登记的 `demo 示例资源`，证明 UI 轮询能跨 Host 重启自愈](backend-resource-restored-20261112.png)

<!-- 20261112-008 -->

## dsh-sqlite 经独立子代理黑盒测试后的修复

（同日，`tests/sqlite.test.mjs` 从 20 项增至 37 项全绿）：①`sqlite_query` 改成**真只读**——写语句/PRAGMA 赋值在打开库前拒绝，执行期再叠一层 authorizer 拒绝全部写动作，读查询不再创建数据库文件；

②多语句脚本默认包事务（自管 `BEGIN/COMMIT` 的脚本除外），失败整段回滚；

### 跨调用不留事务

脚本留下未提交事务就回滚并回 `closedOpenTransaction: true`；③`backup` 在打开源库前校验 target，且**拒绝覆盖任何已打开的库**（含源库自身，否则会静默覆盖正在使用的文件并丢数据）；

④`changes` 改为「本次调用」的 `total_changes` 差值、非 DML 报 0 且不给 `lastInsertRowid`，`totalChanges` 更名 `connectionChanges`（明确含触发器与已回滚行）；⑤重复列名改成 `a`/`a_2`/`A` 不再静默覆盖；

⑥`sqlite_schema` 改用 `pragma_table_xinfo`，生成列可列出；

⑦路径拒绝含 `:` 的相对路径（挡 `file:` URI 与 NTFS 备用数据流），`database` 与 `path` 同传报错，`PRAGMA foreign_keys` 禁止改写，单行超 `maxBytes` 直接报错而不是返回空结果。

**另接入 `@local/backend-resource`**：每条打开的连接登记为 `kind:'sqlite'` 资源（label `main · sqlite/agent.db` / `:memory:`，带 `sessionId`），UI 资源列表可直接关闭（回调 close 并清缓存），插件卸载先 close 再 release；

没装该插件时自动降级。实测经 `GET /backend-resource/state` 看到 `sqlite-1`，`POST /cancel` 后连接关闭、再查同 `:memory:` 已是新库。

<!-- 20261112-007 -->

## dsh-sqlite 增加 **`sqlite_lifespan…

dsh-sqlite 增加 **`sqlite_lifespan_control`**（`op: open|create|close`，第六个工具）：`open` 传 `path` 只打开**已存在**的文件（不存在则报错并提示 create），返回资源 ID 并保持连接，重复 open 同路径返回同一 ID 且 `alreadyOpen: true`；

`create` 传 `path` 创建**新**库并打开（父目录一并建，已存在则报错并提示 open，且不受 `createIfMissing` 限制）；

`close` 传该 ID，经 `backendResources.cancel` 走与 UI 面板相同的取消回调（关闭连接 + 清缓存），没装 backend-resource 时退回本地 ID `sqlite-local-N`。

其余工具隐式打开时仍按 `createIfMissing`（默认 true）决定是否创建。`sqlite_status` 会为已打开的库显示 `open as <id>`。

实测 `open :memory:`→`sqlite-1`、`open scratch/lifespan.db`→`sqlite-2`、重复 open 同 ID、`close` 后文件仍在（只释放连接）、二次 close 报 `No open database with id`、`open` 不存在的文件被拒且不落盘。

**性能实测（`time_perf`）**：同步 SQLite 阻塞 Host 事件循环——20 万行 INSERT ~120 ms、20 万行排序读 ~73 ms、**100 万行 INSERT ~593 ms**，故批量写必须分批；读端靠 `iterate()`+`maxRows` 提前停止。
