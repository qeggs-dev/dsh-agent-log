<!-- 20261114-033 -->

## 新增 DSH 插件 @local/dsh-title（会…

新增 DSH 插件 **`@local/dsh-title`（会话标题）**（工作区 `dsh_plugins/title/`，独立 git 仓库，首提交 30d8c3b，bundle 行 id `title` / entry `include:title`，`install_bundle` 以本地目录装入 desktop profile → `application: applied`、warnings 空）：只注册一个模型工具 **`title`**。

**用户要求原话**「不给参数就是获取，给 set 参数就是设置到新的标题」，因此 `parameters` 只有一个可选 `set`（string），**没有任何必填参数** —— 这是 R-005「每个注册的工具都必须带必填 description」的唯一例外（见 R-018）。

读取走 `ctx.sessionTitle.get(session)`（返回 `SessionTitleSnapshot | undefined`，`undefined` = 该会话还没有合格输入），写入走 `ctx.sessionTitle.rename(session, title)`：追加一条 `session/title` 事件（`source.kind = 'user'`）并**钉住标题** —— 进行中的自动生成被取代、之后自动生成也不再改它（`refresh()` 是唯一解钉入口）。

服务按 `inject = ['tools', 'sessionTitle']` 硬依赖；从 `exec.agent?.session` 取不到活会话时明确报错。

返回（英文）：`ok / action(get|set) / title / hasTitle / previousTitle / source(user|provider|fallback) / sessionId / updatedAt`；

`render` 输出 `Session title: "…"` 或 `Session title set to "…" (was "…")`；`set` 全空白在调用前拒绝，规范化后为空时把服务的 `SessionTitleInvalidError` 翻成英文短句，两种情况都不改动标题。

`isConcurrencySafe: false`（含写操作），`timeoutMs` 15000，`presentCall` 只作卡片标题用（会话日志的调用行不读它，见 20261113-009）。

### 验证

`node --check` + `tests/title.test.mjs` **12/12**（假 ctx：无参读取、空对象、未命名会话、set 往返与 previousTitle、全空白/非字符串/服务拒绝、无活会话、output.schema 与返回字段对齐、参数表确实没有 description）；

实机 `title()` 读到 `注册标题工具插件`（source: provider）→ `title({set: 标题工具 · 冒烟测试})` → `title({set: 注册标题工具插件})` 复原，三次结果均正确。

### 副作用

这次实测把本会话标题从 provider（自动生成）钉成了 user，自动改名不再覆盖它。

### 未验证

插件页里该行的图标与标题文字渲染（本机无浏览器控制）。
