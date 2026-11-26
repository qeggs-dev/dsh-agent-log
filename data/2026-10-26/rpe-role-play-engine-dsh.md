<!-- 20261026-001 -->

## 新项目 **RPE（Role Play Engine）**，形态是 DSH 插件

用户 2026-10-26 定下的三个前提：①进入方式是**「新建 Session 时打开 RPE 开关、让该 Session 进入 RolePlay 模式」**（明确没有选斜杠命令入口）；②**核心问题是「设计一套能根据场景主动把信息注入到 AI 的系统」**，即角色记忆与上下文注入，不是多角色并行；

③交付定位是**「当作可公开的东西做」**（要 README、版本号、示例卡、边界说明）。项目目录、v0 范围、模式开关的具体形态均尚未确定

<!-- 20261026-002 -->

## RPE 的一条运行版硬约束（`cordis_inspect_qu…

RPE 的一条运行版硬约束（`cordis_inspect_query` 实测）：`ctx.systemPrompt.context({ text })` 的 `AssembleContext` 只有 `{ scope?, signal? }`，**拿不到对话内容**；

因此「按场景注入」只能由插件自己监听 `session/event`（agent-bus 已验证该事件可用，能取到 user/assistant 消息里的 text 块）维护 per-session 窗口，再在每次装配时从自己的窗口里选条目。

好消息是 `assemble()` 在**每个 model step 前都会重算**，`PromptContext.text` 也可写成函数每次调用，所以动态注入可行

<!-- 20261026-003 -->

## RPE 核对的四条运行版事实（0.2.1-rc.3，`cordi…

RPE 核对的四条运行版事实（0.2.1-rc.3，`cordis_inspect_query` + 包 README 实测）：①**preset 是静态 entry list，没有「包含另一个 preset」的语法**（`plugins` 是字面数组；

`cordis:include` 只能 include YAML/JSON 文件，而别的 preset 的 plugins 是 declaration 里的一个数组、不是文件）；registry README 明说「用户覆盖会整体替换 child list、不会自动合并」，一个 Agent 只绑定一个 preset。

运行时有 `agentPresets.mount(ctx,id)` / `composeFrom` / `serviceFor`，但把两个 preset mount 进同一 scope 很可能因同名 section（如两套 `deployment:persona-prefix`）而抛错（同层同名重复会 throw）—— **未实测**。

②**动态注入的正确落点是 `systemPrompt.context()` 而不是 `section()`**：context 条目会变成模型历史里的 **user-role 快照**，`refreshContext()` 在 admission 前重新读其文本，`assemble()` 每个 model step 重算。

③新会话与输入区插槽齐备：`conversation.hero.agentPreset`（新建会话的 preset 控件）、`conversation.hero.options`（workspace 与 preset 控件之后的右对齐小控件，仅在有 Session 时渲染）、`shell.overlay`（全帧浮层，模态框放这）、`conversation.composer.dock` / `conversation.input.dock`（输入框下方/上方常驻条目）、`main`（keyed，可加独立面板页）。

④`read` 工具现在**能**直接读 `app.asar` 内的文件（本次读到了 preset / registry / system-prompt 三个 README），但 `glob` 与 `rg` 对 asar 仍失败（os error 3）—— 所以查 asar 内文件只能靠已知路径 + read，不能靠检索

<!-- 20261026-004 -->

## 双预设 spike 结论（读 `dsh-agent-preset-registry/lib/index.js` 得出，未安装任何东西）

①一个 Agent 只绑一个 preset —— `join()` 用 `bindScopeParent(key, generation.key)` 给 agent 的 scope 设**唯一父 scope**，换 preset 走 `binding.parent.rebind(generation.key)`（覆盖，不是叠加）；

所以「RPE preset 之下再叠一个 preset」在运行时结构上不可能，只能**生成时合并**（把副预设的行并进 RPE preset 的 plugins 再声明；改副选项=重新生成+覆盖 preset 行，HMR 只对新会话生效，已在跑的会话保留旧 revision）。

②**preset 只能对空白会话变更**：`select` 写 `agent-preset/selected` 事件、经 `agentPreset` session projection 持久化，README 原文「A session may still change preset while it is blank」——即「RPE 开关」在会话发出第一条消息后就锁定，中途开关只能是插件层软关闭（注入器停手、工具仍在），preset 层做不到。

③因此「开关 = 主 preset 是否为 RPE」的投影是唯一与框架真值源一致的实现，任何独立 per-session 布尔都会与它脱节

<!-- 20261026-005 -->

## RPE M0a/M0b 已交付并装机

（`D:\Projects\Deepseek_Harness_Workspace\rpe`，包 `@local/dsh-rpe` 0.1.0，desktop profile 的 bundle；preset 行 `preset-rpe` / `config.id: rpe` / 显示名「角色扮演」/ order 19）。

### M0a

只含 RPE 行的 preset，用户已在新建会话的模式列表里确认「角色扮演」正常出现。

### M0b

先试 `cordis:include` 内嵌**失败**（原因见 `id:20261026-006`），最终改为**生成时内联合并**——`tools/build-embedded.mjs` 从 `dsh-desktop-presets/generated.patch.yml` 的 `collab` 声明切出 19 行，直接写进 `cordis.patch.yml` 的 preset 声明（保留 `!!js` 与 block scalar 相对缩进）；

生成器规则用 11 项回归测试钉住（`node --test --test-isolation=none "tests/*.test.mjs"` 全过）。`index.js` 只提供只读工具 `rpe_status`，零 `@deepseek-ai/*` 依赖；

另加 profile 层的 `doctor.js`（见 006）。

### 两条操作事实

①改 bundle 的 `cordis.patch.yml` 必须重启（`set_bundle` 开关不重读它；`install_bundle` 对已装版本直接返回 `already-installed`）；②示例空间在 `rpe/spaces/demo/`（巡林人·砚 + 一条设定 + 场景态）

<!-- 20261026-006 -->

## RPE 的两个机制结论 + doctor 通道

①`cordis:include` 在 preset 里**不能用**——`config.path` 是 URL 不是路径（实现为 `fileURLToPath(new URL(config.path, ctx.baseUrl))`，裸 `D:/...` 解析成 scheme `d:`，报 `The URL must be of scheme file`；

写 `file:///D:/...` 后又变成 24 行全 `never started`：include 是 `EntryGroup`，预设注册表在 group 的子行拿到 fiber 之前就审计，`auditRows` 把 `entry.fiber === undefined` 当硬失败，而 `activate()` 失败即 dispose 整棵树、`broken` 是终局）。

**结论：preset 里组合另一个 preset 只能把行复制进声明**，代价是改子模板要重新生成 + 重启。

②新增 `@local/dsh-rpe/doctor`（profile 层行，`preset.json` 的 `doctor: true` 生成），启动后 1.5s 把 `agentPresets.list()`（含每个预设的 `broken` 文本）写到 `rpe/doctor.json`——这是 Agent 侧唯一能看见「预设为什么坏」的通道，GUI 里坏预设很容易被误认为「没装」。

### 实测

修好后 `rpe` 无 `broken`。③用户 2026-10-26 追加两条行为要求，归 M3 客户端层：**强制开启 RPE 但未加载 RPE preset 时必须保险关闭**；**正常开启 RPE 的会话要在标题栏显示 RPE 图标**

<!-- 20261026-013 -->

## RPE M0 验收完成（双向，不需要用户动手）

①RPE 会话 `session-bf545806-fd7a-40f8-80b2-c80aef698eb9` 实测工具表 = `rpe_status` **加** collab 那 19 行的全部工具（pwsh / read / edit / subagent / workflow / present / skill …）→ 子模板并集成立；

②同一工作区的普通 collab 会话（本会话）`Tool.listTools` 里**没有** `rpe_status` → 「关掉不影响正常会话」成立；③`rpe_status` 真实输出「1 个空间 / 1 角色 / 1 设定 / 有场景态 / 无记忆库」。

### 一个易误判点

该 RPE 会话的 `get_session_metadata` 仍报 `preset: collab`，因为它是**空白期**切到 rpe 的（header 是创建时事实，投影才是当前值）——判断会话实际模式要看工具表，不能只看这个字段。

### 验收方法可复制

`list_sessions` 找会话 → `send_session_message` 让它做事 → `sleep` → `read_session` 读回；M1 及以后都照此自验，不必再请用户手点

<!-- 20261026-027 -->

## RPE M1a 完成（纯逻辑 + 真机检索验证）

新增 `rpe/src/{config,corpus,score,embed,vectors}.js` 与 `tools/probe.mjs`，单测 23 项全过（生成器 11 + M1a 12）。

实测（demo 空间，3 条目，1024 维）：问「这条山路通到哪里」，三条 route **都只注入** `scene` + `lore:mountain-path`——本地 0.6121 / `cloud-same` 0.6099 / `cloud-big` 0.4941（同排序、不同绝对分 → `minScore` 必须按 route 标定，全局一个值会一边注噪一边什么都不注）；

### 索引复用实测

第二次运行「新嵌入 0 条，复用 3 条」，且同款 0.6B 的云端与本地分差仅 0.002。

### 过程中发现并修正一个真设计错误

把「正在说话的角色卡」放进检索池后，`cloud-big` 会把角色卡（0.5575）排在设定（0.4841）之上——角色卡是**身份**不是可检索事实；`selectEntries` 增加 `activeCharacterId` 排除说话者，其余角色仍可被检索（NPC 该被提起时还得提起）。

另 `saveCache` 必须 `mkdir -p`，否则首次运行必然 ENOENT

<!-- 20261026-020 -->

## 界面端口镜像补了常驻开关

（同一插件）：侧边栏底部 `sidebar.footer.action`（id `ui-port-mirror`，order 10，和 Settings 同一行；`wide=false` 时渲染 32px 圆点按钮）随时开关，不必进设置页；关方向仍是两步确认（首点「确认关闭？」6 秒可撤销），开方向单击。

它每 15 秒回读 `/ui-port-mirror/state`，所以设置页里改过的状态不会失真；停止时若这条请求本身走镜像，会等 700ms 回读状态再定论。

### 两条实测

①**只要 bundle 里已有 `dsh.client` 声明，之后改 client.js 可以热生效**——改完 `set_plugin` 关再开，`Slots.listSubTree({root:'sidebar.footer.action'})` 的 occupants 立刻出现该行（active true），不用重启 App（与 `id:20261026-015` 说的「新增声明要重启」不冲突：那条讲的是**首次**加声明进 boot graph）；

②`slots.inject(ownerKey, cb)` 的 ownerKey 就是 slot 名本身，不需要把 `@deepseek-ai/dsh-client-ui-sidebar` 写进 `dsh.client.inject`

<!-- 20261026-021 -->

## 端口镜像改成事件推送（SSE），不再是轮询

`GET /ui-port-mirror/events` 是 `text/event-stream`，连上先发一帧全量 state，之后每次 applySettings 结束（含失败分支）`broadcast()` 推一帧；25 秒发一次 `: ping` 注释帧防代理断流；

客户端用 `EventSource` 订阅，`onerror` 时退回 15 秒轮询、`onopen` 时再撤回。设置页与侧边栏开关共用这条流，所以任一处改动另一处立刻同步。

### 两个踩坑点

①**带 `event:` 字段的帧不会触发 `EventSource.onmessage`**，只走 `addEventListener('事件名')`——第一版发的是 `event: state`，客户端 onmessage 收不到任何东西（HTTP 层看帧完全正常，容易误判）；改成只发 `data:` 才对。

②自己写的测试脚本按 `\n\n` 切帧时，首帧前面有 `retry: 2000`，用 `frame.startsWith('event: state')` 会把它整帧丢掉。

### 方法论结论

Host 侧的 `ctx.on/emit` 事件全是**进程内**的，框架里没有任何一条把 Host 事件送到浏览器的通用通道（只有 typert `@Remote` 生成的调用/流，需要装饰器 + schema 代码生成，纯 JS 本地插件做不到），所以「让 UI 感知 Host 状态」只能自己开一条推送通道（SSE 最省事），或者退回 HTTP 拉取
