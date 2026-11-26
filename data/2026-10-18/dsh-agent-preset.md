<!-- 20261018-002 -->

## 桌面版 DSH 已从 0.2.0-rc.2 升到 **0.2.1…

桌面版 DSH 已从 0.2.0-rc.2 升到 **0.2.1-rc.2**（`app.asar` 内 `dsh/package.json` 与抽查的 `@deepseek-ai/*` 均为 0.2.1-rc.2），**内置提示词变量只剩 `provider` 与 `model`，`cwd` 已被移除**：0.2.0 的 dsh-system-prompt README 写「循环提供 model 与 cwd」，0.2.1 改为「provider 和 model」并明文要求从 preset 的 persona 中删掉 `Your working directory is {{cwd}}.`；

未注册变量在 `renderPrompt` 阶段**抛错**（用安装版代码实测：`unknown prompt variable "{{cwd}}" in section "deployment:persona-prefix"; registered variables: provider, model`），所以症状是**整个提示词组装失败、请求发不出去**，不是显示字面量。

故 profile patch 里 8 个自建预设（collab / plan / introvert / pity / slacker / discuss / confident / gossip，其 persona 文本都含 `{{cwd}}`）在 0.2.1 下全部不可用，而 `selectedDefault: collab` 让默认新会话直接撞上；

`{{model}}` 仍正常。工作目录现由 working-directory 服务以**必需的 runtime context** 提供（不会被 `suppressRuntimeContext()` 移除），删掉该半句即可。

注意 `dsh-desktop-presets\generate.mjs` 的 persona 源除 `personas\*.txt`（仅 collab/discuss/confident/gossip 有）外还回落到旧 `.agent-presets\<id>\agent.cordis.yml`（plan/introvert/pity/slacker 无 txt 覆盖），只改 live patch 而不改这些源，重跑 `--append` 会把 `{{cwd}}` 写回去。

### 已于 2026-10-18 同日修复

live patch 的 8 处与 `personas/{collab,discuss,confident,gossip}.txt` 均已删掉该句，`generate.mjs` 另加两道防线（生成时剥离旧源里的 `{{cwd}}`、生成后校验只允许 `model`/`provider`），`generated.patch.yml` 已重跑，两个测试与 8 份 persona 的 `renderPrompt` 实测全部通过；

改前备份在 `.tmp/cordis.patch.yml.bak-20261018`。

另：0.2.1 的 shipped standard 已去掉 `tool-ralph` / `tool-subagent-claude-code`、新增 `time-context`，而生成器仍固定抓 0.2.0-rc.2 的 standard 缓存（这些行在预设里都是 `disabled: true`，暂不致错）
