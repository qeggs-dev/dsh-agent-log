<!-- 20261101-002 -->

## 新增桌面版插件 **`@local/dsh-tool-ask-a…

新增桌面版插件 **`@local/dsh-tool-ask-approval`**（源目录 `〈工作区〉/dsh-tool-ask-approval`，bundle 行 id `tool-ask-approval`，desktop profile，`install_bundle` 返回 `application: applied`，warnings 为空）：把 Host 审批接缝 `ctx.approval.request` 原样包成模型工具 `request_approval`——参数只有一个 `content`（任意文本，作为 `reason` 原样成为浏览器审批卡片正文），返回 `{ outcome }` ∈ `allowed-once` / `rejected` / `cancelled` / `unavailable`；

**工具自身不改任何权限或会话状态**，批准与拒绝都算调用成功（结果文案直接说明）。

### 实现要点

`inject: ['tools','approval']`、`ctx.effect(() => ctx.tools.register(...))`、传 `exec.signal`（回合被取消则 `cancelled`）、**故意不传 `callId`**（传了浏览器会多渲染一块工具详情，卡片正文就不只有调用方文本了）；

**模型侧文案一律英文**（用户 2026-11-01 要求：反馈文本让模型当指令读更可靠），卡片正文则随 `content` 用用户语言。

### 实测

`Tool.listTools` 已出现该工具；当时本会话审批策略被用户切成 `never`，调用立即返回 `rejected`（服务在派发应答方之前确定性拒绝，`approval/asked` + `approval/decided` 仍会写入会话日志）；**卡片渲染路径未验证**，需要策略为 `ask` 时再试。

另：改完 `index.js` 后宿主仍缓存旧模块（子代理探测读到的仍是旧中文文案），必须 `restart_dsh` 才换新模块代次；重启后以 `Tool.listTools` 里出现英文 description 作为「新模块已生效」的判据。

<!-- 20261101-011 -->

## 新增桌面版插件 **`@local/dsh-readable-p…

新增桌面版插件 **`@local/dsh-readable-preset`（「可读预设」）**（源目录 `〈工作区〉/dsh-readable-preset`，bundle 行 id `readable-preset`，desktop profile，`install_bundle` 返回 applied、warnings 空）：把 AgentPreset 当文件来读/装/卸。

### 三个全局工具

全局＝任何预设里都能调用，包括 chat 这种零工具组装，空会话靠它自举：`list_agent_presets`（列出全部预设：id/名称/描述/是否默认/是否可激活＋**每个预设会组装出的工具名**）、`load_agent_preset`（真正重绑组装，并把该预设声明全文含 persona 当工具结果交给模型）、`unload_agent_preset`（只撤能力，提示词留在历史里）。

### 界面

会话标题栏 `conversation.session.header.actions` 槽 order **-9**（现有 `agent-preset` 标签是 -10）的 `+` 按钮 + 已加载时的模式图标，菜单里是「名称/描述/工具数」，点图标即卸载。

两条路径共用同一份 Host 操作（HTTP `/readable-preset/{token,state,presets,apply}`，token + Origin 校验）。

工具注册与槽位均已用 `Tool.listTools` / `Slots.listSubTree` 确认（occupant `readable-preset` active）。

<!-- 20261101-012 -->

## 可读预设插件的四条实现事实（都踩过或实测过）

①**加载＝`ctx.agentPresets.recompose(agent.ctx, id)`**，绕过 `select()` 的「会话已开始就锁」检查——这是本插件存在的前提；

系统提示词与工具都会切，工具增删由 agent loop 自己写 `developer/message` 的 tool-addition / tool-removal。

②**基线必须取 `agentPreset` 投影**（`ctx.sessionProjections.stateOf(agent.session,'agentPreset')`），**绝不能用 `session.header.agentPreset`**：本会话实测 header=collab 而投影=cordis（新会话首轮前合法换过预设），拿 header 当基线会把这种正常情况误判成「已加载」并让卸载回到错误预设——第一版就是这么错的，已修，重启后 `/state` 返回 baseline=cordis / loaded=false。

③**不追加 `agent-preset/selected`**：加载状态不写日志，故不跨进程存活（重启＝自动卸载），但卸载总能精确回到投影里的预设。

④工具清单＝`acquireScope(id)` + `tools.schemas(lease.key)`（该作用域＝全局层＋预设行，实测 minimal 31 / cordis 61 个）。

### 验证

子代理端到端跑通 list→load minimal（其可见工具 60→30）→list（标 running）→unload→list；HTTP 四条路由均 200，no-op load/unload 正确。**界面渲染未肉眼验证**（无浏览器控制）。

改 index.js 后仍需 `restart_dsh`（模块缓存）。
