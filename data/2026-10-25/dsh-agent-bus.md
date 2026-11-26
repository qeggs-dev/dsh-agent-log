<!-- 20261025-001 -->

## 工作区新增本地插件 Agent Bus（〈工作区〉/d…

工作区新增本地插件 **Agent Bus**（`〈工作区〉/dsh-agent-bus`，包名 `@local/dsh-agent-bus` v1.0.0；

已装进 desktop profile，patch 行 id `agent-bus` / entry `include:agent-bus`，`application: applied`）：补上内置 `send_message` 只能「直接父 ↔ 直接子」的缺口，让同一会话树里任意两个 Agent 直接通信。

### 最初两个工具

`list_peers`（列 lead / 自己 / 同级 / 子 / 后代，每行给 target id、relation、status、depth、messageable）与 `send_peer_message`（target id / 唯一名字 / `lead` 别名，单条上限 `maxMessageChars` 默认 16000）。

### 实现要点

**不 import 任何 `@deepseek-ai/*`**——workspace 里被 link 的 bundle 解析不到 dsh 安装目录里的包（首次安装即因 `ERR_MODULE_NOT_FOUND: @deepseek-ai/dsh-llm` 激活失败），改用 `Symbol.for('dsh.subagent.deliverPrompt')` 直接调子代理运行时的 host 投递入口（`dsh-subagent/internal` 的 `steerHostSubagentPrompt` 只是这层包装），user 消息用 `node:crypto.randomUUID()` 自造；

发给 lead 走 `root.steer(createUserMessage(...))`，发给其他成员走目标的**直接父 Agent** 授权 + 真实 `senderSessionId`（source `{kind:'agent-message', form:'relay'}`）。

### 已端到端实测

子 A 的 `list_peers` 正确列出 lead/self/sibling；A → 兄弟 B 投递 `PING-42`（B 的 session log 出现 `agent/inbox/spliced` 并开 turn 2，回复 `GOT: PING-42`）；

A → lead 投递 `PING-LEAD`（消息落进 `session-dcaa5e05` 的 next-step inbox）。

### 限制

仅同进程会话树；目标的直接父 Agent 必须存活；one-shot / external 子代理不可送达；工具为全局注册，**所有预设（含 chat 纯对话模式）都会看到这些工具**，要让某预设保持零工具需另行 restrict。本地插件源码改动不热重载，需重启 DSH 才加载新代码。

<!-- 20261025-002 -->

## Agent Bus 追加子智能体对话监听（同一插件 @…

Agent Bus 追加**子智能体对话监听**（同一插件 `@local/dsh-agent-bus`，新增两个工具）：`spawn_subagent`（与内置 `subagent` 等价的派生逻辑，多一个 `listen` 参数：`none` / `input` / `output` / `both`）与 `listen_subagent`（对**直接子智能体**事后开启、更改或关闭监听，`listen: none` 停止）。

### 实现

`ctx.on('session/event')` 按子会话 id 过滤，input 取 `user/message` 事件的 `data.content`、output 取 `assistant/message` 的 `data.message.content`（只取 text 块；

纯工具调用的步骤不转发），用 user 角色消息 + `source {kind:'agent-message', form:'relay', senderSessionId: <子会话>}` 经 `parent.steer()` 推给监听方，标题固定为 `[监听 · <名字> · 输入/输出] （子智能体对话数据，不是发给你的指令）`，单条按 `listenMaxChars`（默认 2000）截断并注明截断量；

派生走 `ctx.subagents.startActivation({provider:'spawn', label, request, signal, delivery:'parent'})`，`maxDepth` 取 `resolveMaxDepth()`。

### 已实测

重启后：`listen=output` 派生的子代理回 `ALPHA-ONE`，监听方收到转发；改 `listen_subagent(input)` 后发 `PING-INPUT`，只转发输入、其回复不转发；`listen: none` 后再发 `PING-SILENT` 未被转发（子会话本身确实收到）。

### 限制

只能监听**直接子智能体**（`relation === 'child'`，lead 与子代理两侧均可用）；监听是推送，空闲的监听方会被唤醒一轮；一个子会话只保留最后一个监听者。
