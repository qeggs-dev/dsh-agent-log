<!-- 20261026-011 -->

## 会话桥接追加三个工具

（同一插件，仍然是 `@local/dsh-session-bridge`，配置新增 `maxListedSessions` / `markSender`）：`send_session_message({sessionId,text,delivery?})`、`list_sessions({scope?,limit?})`（**每行带会话名字**）、`get_session_metadata({sessionId?})`（省略 id = 查自己）。

### 五条实测事实

①`SessionSummary` 里**没有 title**——名字是 projection：`list_sessions` 按代价从低到高取 `summary.projections.values.title` → `sessionController.projections({sessionId}).values.title`（字段可能是字符串或 `{val}`/`{value}`）→ 最后才扫日志里的 `session/title` 事件；

三条路径都失败才显示「（未命名）」。②`summary.agentAvailable` **不代表活着**：冷会话（persisted、可 resume）它也是 true，最初据此判 live 导致列表把冷会话标成「空闲」；

正确的 live 判据是 `ctx.sessions.get(id) !== undefined`（或 `ctx.agents.get(id)`），改后冷会话正确显示「未加载」。

③`send_session_message` 走 `sessionController.prompt({requestId, sessionId, mode: 'queue'|'steer', content}, signal)`——这个入口**没有 sender 字段**，目标会话看到的就是一条普通 user 消息（`source.kind='user'` + rpcId），所以插件默认在正文前加 `[来自会话 <调用方 id>]`（`markSender: false` 可关）；

目标未加载时这条消息会把它唤醒（实测 `wokeCold: true`）。

④**已归档的会话会吞掉消息**：`prompt` 返回 accepted，日志里 `agent/inbox/spliced` 与 `turn/start` 都正常写入，但紧接着 `turn/end {kind:'blocked'}`、没有任何 model step、也没有回复（实测目标 `session-89937820` 就在 `workspace.json` 的 `global.archivedSessionIds` 里；

`session-9a9a7f3b` 未归档，同样流程回复了 `BRIDGE-OK`）；Host 侧**没有查询归档集合的 getter**（只有 `archiveSession`/`unarchiveSession`），所以只能在工具描述里写明、无法预检。

⑤`get_session_metadata` 的权限/模型**要从日志折**：冷会话读不到 projections 的 `sandboxMode`/`permissions`/`modelSelection`（会显示「未显式设置」），改为扫 `sandbox/mode`、`approval/policy`、`request/header` 事件后，冷会话正确显示 `workspace-write / never` 与 `deepseek-official/deepseek-flash`。

### 已实测

`list_sessions` 的 `scope: live` 只列常驻会话、`all` 按时间列出 213 条且名字齐全；`send_session_message` 带前缀投递 → 对方回 `BRIDGE-OK` → `read_session` 能读到这两条；

`get_session_metadata` 对自己与冷会话都正确。

<!-- 20261026-012 -->

## `list_sessions` 改为默认「全部列表」

（同日第三次调整）：默认列出**全部工作区**的会话（实测 407 条，覆盖 7 个工作区）、**按 `updatedAt` 倒序**（不再「运行中优先」）；`workspace` 参数按工作区筛选（标题 / 目录路径 / id 三选一，找不到时错误里列出全部工作区及其 id 与路径）；

`limit` 默认 30、上限 100（配置 `maxListedSessions` 同步改 30）；`scope` 默认 `all`；

新增 **`currentWorkspaceOnly: boolean`**（默认 false）用来还原旧的「只列当前工作区」行为，与 `workspace` 同时给出时以 `workspace` 为准。

### 实现

`sessionController.list()` 一次拿全量 summary，用 `workspaceRegistry.list()` 的 `sessionIds` 建 sessionId→workspace 映射（`owned`），未归属的会话再按 `cwd` 与工作区路径比较；

每行加 `workspace` 字段（工作区标题）并在 render 里显示。

### 实测

默认 6 行时间从「2 分钟前」到「58 分钟前」单调递减；`workspace: 'DSH-QQBot'` 返回该工作区 9 条；`currentWorkspaceOnly: true` 与 `workspace: 'Deepseek_Harness_Workspace'` 都返回 213 条；

未知工作区错误里正确列出 7 个工作区。

### 遗留

修复 `workspaceId` 之前用 `cwd` 建的 3 个测试会话不在任何工作区 `sessionIds` 里，全量列表里没有工作区标签（但同路径的 workspace 过滤仍能命中它们）。

<!-- 20261026-010 -->

## 新插件「会话桥接」

（`〈工作区〉/dsh-session-bridge`，包 `@local/dsh-session-bridge` v1.0.0，desktop profile bundle，行 id `session-bridge`，`application: applied`）：一半是 Client（输入框左侧 `conversation.input.left` 里 id `session-id-copy` order 10 的紧凑控件「会话 ID」，点击复制当前 Session ID，就地显示「已复制/复制失败」1.6 秒，悬停标题带完整 id），一半是 Host 工具 `read_session({ sessionId, limit?, includeToolCalls? })`。

### 三条运行版事实

①**新增 `dsh.client` 声明必须重启一次才进 boot graph**——安装后 Host 工具立刻可用，但 Client 半要重启；

重启后 `Slots.listSubTree({root:'conversation.input.left'})` 的 occupants 才出现 `session-id-copy`（active true）。

②`sessionController.inspect(id, signal)` 是**冷读**：返回 `{meta: SessionHeader, inheritedEventCount, events}`，不 resume Agent、不发消息；适合跨会话读取。

③注入上下文也走 `user/message`，但 `source.kind` 不同——实测有 `agent-instructions` / `runtime-context` / `skill-catalog` / `time-context`，真正的对话是 `source.kind === 'user'`（人）或 `'agent-message'`（其它 Agent）；

`read_session` 就按这个过滤，只收这两类 + `assistant/message` 的 text 块，`includeToolCalls` 时再加 `tool/call`。

### 产品已自带复制入口

会话列表「…」菜单的 shipped 行 `session-id`（order 450）+ toast kind `sessionIdCopied` / `sessionIdCopyFailed`，所以本插件的按钮是补在会话视图里、不替代它（再写菜单行会重复）。

### 访问边界

默认只允许同一工作区，用 `workspaceRegistry.resolveByPath(cwd)` 把双方解析成工作区比 id（目录未注册时退回规范化路径比较），跨区需配置 `allowCrossWorkspace: true`。

### 已实测

读本工作区的 `session-89937820-…`（2 条）与 `session-9a9a7f3b-…`（4 条，含 `write`/`read` 工具行）正常；读 `〈项目目录〉/QQBot/DSH/Workspace` 下的会话被拒并给出原因；不存在的 id 报「找不到会话」。

### 未验证

按钮点击写剪贴板（无浏览器控制，只能确认注册生效）。Client locale 用 `locale.register(ns, locale, dict)` 注册 zh / zh-CN / en / en-US 四份字典再 `locale.bind(ns)`；配色只用 `--dsw-alias-*` 主题变量。
