<!-- 20261026-028 -->

## 新插件「Active memory」

（`〈工作区〉/dsh-active-memory`，包 `@local/dsh-active-memory` v1.0.0，desktop profile bundle，entry `include:active-memory`，`application: applied`）：主动记录 + 被动读取。

`memory_record` 按 mode 存 RolePlay（emotion/scene/event）或 Work（item/solution/fallback/communication）；

JSONL 存 `<cwd>/.dsh-active-memory/memories.jsonl`（或 global `<DSH_HOME>/active-memory/`），向量 1024 维随条目保存。

检索从最新用户消息向上扩窗，窗口每轮 +1、阈值每轮降 `similarityDecayPoints` 个百分点（默认 4，即 0.04），命中数 ≥ `countThreshold`（默认 3）且库条目数 ≥ 3 才注入，否则什么都不注入。

默认 `embeddingProvider:auto`：Ollama `qwen3-embedding:latest` `/api/embed` → OpenAI-compatible（有 key 时）→ 本地 hash fallback（独立阈值 0.12）。

### 工具

`memory_record` / `memory_search` / `memory_list` / `memory_forget` / `memory_status`。

### 一条重要运行版修正

动态注入必须用 `ctx.systemPrompt.context()`，不能用 `section()`——agent-loop 在 `agent/pre-step` 之前就 `assemble()` 静态 sections，而 `step()` 会用 `refreshContext()` 重读 context；

用 section 会晚一个 model step，实测 turn 2 第一步看不到注入、第二步才看到。改用 context 后 turn 4 第一步的 runtime-context 里即出现 `[Active memory · 自动检索]`。

### 测试

logic 15 + storage 5 + 真 Ollama host-harness 1 + roleplay 1 + live-ollama 1 全过；

e2e 会话 `session-8c8da26a-1561-4f89-9bdd-dedf4ed8ed27` 实测 3 条 Work 记忆：第二轮 `outcome=injected / rounds=1 / threshold=0.58 / hits=3`，重新加载插件后的第四轮 `outcome=injected / rounds=2 / threshold=0.54 / hits=3`。

### 未验证

Plugin Manager 卡片/图标真实渲染（无浏览器控制）。
