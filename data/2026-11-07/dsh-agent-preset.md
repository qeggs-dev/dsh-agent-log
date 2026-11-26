<!-- 20261107-001 -->

## 桌面版致命恢复会「搬走」整个 profile patch，这就是自建预设消失的真因

（0.2.2-rc.1 代码与现场双重确认）：启动期致命错误对话框的第三个按钮原文是「禁用第三方插件、备份 profile patch 并重启」，实现是 `DesktopProjectManager.disableAllPlugins()` → `sanitizeProfile()`：把 `<profile>\cordis.patch.yml` **重命名**为 `cordis.patch.yml.bak-<Unix 毫秒>`（不是复制），再把 `dsh.profile.bundles` 重置成 shipped web 模板 `[base, web-app]`；patch 缺失后由 `initProfile` 重新生成为模板（3 行注释 + `[]`），之后 GUI 设置写回只补 `ui-chat` / `ui-settings` / `ui-settings-account` 三行。**用户自建的 6 个预设只存在于该文件的 `- insert: preset-*` 行里**（chat 9 / collab 10 / discuss 15 / gossip 17 / investigate 18 / inquiry 19），所以这个操作＝预设 + 全部 patch 级配置（模型表、permission presets、`agent-preset-registry` 的 `default/selectedDefault`、ui 偏好）一次性从 GUI 消失；rpe「角色扮演」这类由 bundle 自带的预设则不在此列，它随 bundle 被关掉而消失。**2026-11-06 23:40:31 就是这么丢的**：23:39:44 / 23:40:27 / 23:40:44 三次启动崩溃 `Error: desktop welcome: Web authentication failed`（报告在 `%APPDATA%\@deepseek-ai\dsh-desktop\logs\crash-*.log`），恢复按钮在 23:40:31 把 patch 备份成 `.bak-1793979631010`（87,647 B，预设齐全、mtime 16:39:54 即事发前状态），00:30:19 重新启用 17 个 bundle，00:45:21 新 patch 只剩那三行。**恢复＝把该 .bak 直接 copy 回 `cordis.patch.yml`（patch 层有 HMR，新增行立即生效）；结论：不是预设机制 bug、也不是谁删了文件，下次崩溃别选第三个按钮，或先把 patch 拷出来。**

<!-- 20261107-002 -->

## 用户先决定**不恢复** 2026-11-06 崩溃恢复时搬走的…

用户先决定**不恢复** 2026-11-06 崩溃恢复时搬走的 profile patch（理由：那次「清理」正好合意），只要求补回**对话模式**；补回后当场又改主意（「那算了，还是去掉吧」），随即用未改版备份 `cordis.patch.yml.bak-before-chat-20261107-020553` 还原，patch 回到 660 B（SHA256 与改前一致）。实测**删除 `- insert: preset-chat` 也会 HMR**，只是比新增慢一拍：约 2 秒后 live 树的 `include:preset-chat` 才消失、预设列表回到 4 个。chat 的完整声明仍留在 `cordis.patch.yml.bak-1793979631010` 第 598–628 行，想要时原样追加即可（含 order 9、只挂 persona、`complete: true`、`includeRuntimeContext: false`）。**注意：chat 现在不是字面意义上的「零工具」**——它只声明 persona，实测工具表却有 26 个，等于 `minimal` 去掉 `pwsh` + `read_image`，剩下的是 bundle 级插件（dsh-tool-sleep / dsh-super-workspace / dsh-session-utils / dsh-readable-preset / dsh-deepseek-balance / dsh-quick-restart / dsh-tool-ask-approval / dsh-agent-bus …）注入的，这批工具对所有预设都在；预设的 `plugins` 只能增删自己声明的行，够不到根级 bundle（2026-10 写 chat 时本地 bundle 还少，所以当时真的接近 0 工具）。所以「纯对话」只能靠 persona 措辞约束，不能靠「不写行」实现；persona 里「这个会话没有挂载任何工具」这句现已与事实不符，用户未要求改。

<!-- 20261107-004 -->

## 新增桌面版插件 **`@local/dsh-preset-swi…

新增桌面版插件 **`@local/dsh-preset-switch`（「预设切换」）**（源目录 `D:\Projects\Deepseek_Harness_Workspace\dsh-preset-switch`，bundle 行 id `preset-switch`，desktop profile，`install_bundle` 返回 applied、warnings 空）：会话中途**切换主 Agent Preset** 的模型工具 `switch_agent_preset`（参数只有 `id`，省略＝配置里的默认预设）。实现链＝`agentPresets.resolve(id)` → 拒 `broken` → **`recompose(agent.ctx, id)`**（绕过 select 的「会话已开始就锁」）→ 用 `acquireScope(id)` + `tools.schemas(scope)` 读切换前后的工具表（含全局层）→ **`agent.inject(createUserMessage({...}))`** 投递一条 `[preset-switch]` **插件通知**（`source: {kind:'preset-switch', form:'notice', summary}`），内容是 旧→新 预设、工具增删与当前工具表、以及新预设的**完整声明（含 persona）**；工具结果只留摘要，声明正文在通知里。`createUserMessage` 是本地 4 行等价实现（`{id: randomUUID(), role:'user', content, source}`）——link 的 bundle import 不到 `@deepseek-ai/dsh-llm`。**不写 `agent-preset/selected`**：切换只作用于运行时组装，重启即回记录中的预设，切回旧 id 即等于卸载。实测（子代理端到端）：`cordis` 61 工具 → `minimal` 29 工具（0 added / 32 removed，通知逐条列出），通知在**下一个 step** 作为用户侧消息被读到，同目标重复调用返回 nothing was rebound 且不再发通知。`agent.inject` 缺失/抛错时把通知正文退回拼进工具结果。
