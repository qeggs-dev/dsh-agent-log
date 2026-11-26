<!-- 20261001-004 -->

## 目录式预设是旧版写法，桌面版不读

`<DSH_HOME>\.agent-presets\<id>\`（内含 `preset.yml` + `agent.cordis.yml`）属于 0.1.0-rc.5 及更早的复数包 `@deepseek-ai/dsh-agent-presets`；

因此此前建的 7 个模式（collab / plan / python / introvert / pity / slacker / chat）在桌面版的模式列表里**一个都看不到**（用户已实测确认），这些目录可留作参考但需按新格式重写

<!-- 20261001-005 -->

## 0.2.0-rc.2 的 persona 行（`@deepsee…

0.2.0-rc.2 的 persona 行（`@deepseek-ai/dsh-persona`）config 键为 `prefix`（**必填**）/ `suffix`（默认空串）/ `complete`（默认 false）/ `includeRuntimeContext`（默认 true），旧版的 `text` 键已不存在；

`complete: true` 表示这段文本独占系统提示词（不再注入 AGENTS.md 与工具用法指引）

<!-- 20261001-006 -->

## 已为桌面版新建**对话模式**（config.id `chat`…

已为桌面版新建**对话模式**（config.id `chat`，patch 行 id `preset-chat`，order 9）于 `profiles\desktop\cordis.patch.yml`：`plugins` 只有一条 persona（`complete: true`、`includeRuntimeContext: false`），故该模式工具表为空；

persona 文案声明本会话不挂任何工具、只能输出文字，并说明能力不足时直说而非编造

<!-- 20261001-014 -->

## 桌面版 profile patch 的热生效边界（**实测修正**）

①**新增行**（顶层 `- insert:`）HMR 立刻应用——注入后 live 树里马上出现 `include:preset-chat`、`include:temp-root`；

②**改已有行的 config 也热生效**（无副作用探针实测：先摘掉 temp 根的 FullControl ACE，再给 temp-root 行注入一个插件不认识的 `probe: 1` 键，8 秒后插件重新 apply、ACE 被自动补回）；

③**真正不热生效的是 `file://` 插件文件的源码改动**——模块被缓存，只有重启 App 才会重新 import（早先「加了 `ensureFullControl` 却没生效」正是这个原因，当时判断错了：那一次 row 确实重跑了，但跑的是内存里的旧模块）。

### 结论

改 persona / 改 patch 里的配置直接写即可；改 `dsh-temp-root` 这类本地插件源码才需要重启

<!-- 20261001-020 -->

## 协作模式（collab）persona 追加规则（用户 2026…

协作模式（collab）persona 追加规则（用户 2026-10-01 要求）：**没有要求行动时先分类请求**——若属于知识型任务（概念 / 原因 / 对比 / 建议 / 原理，关于本仓库或任何其它东西），就直接、完整地用对话回答，不走「先对齐再等确认」的循环、不附带改动方案、不追问是否继续；

只有会留下痕迹的请求才进入讨论-确认-动手流程，收尾句同步改为 "a knowledge question gets an answer, not a plan"。

**2026-10-01 追加第二段要求：用户还没要求行动前绝不主动行动**——新增 "Do not initiate action." 整段：发现旁边的问题、顺手能改的小事、跑条命令就能确认的事，都只能说、不能做；未获授权的工作即使"明显正确、微不足道、他肯定想要"也不算数；

知识型回答以答案结束，不追加edit/命令/自主启动的子代理；

"What is NOT permission" 列表补了「自认为显而易见 / 微不足道 / 肯定想要」「顺手发现的问题」「想替用户省一个来回」，收尾句补 "including acting because you noticed something they did not ask about"。

persona 现由工作区文件 `dsh-desktop-presets\personas\collab.txt` 维护（2421→3141→4153 字符），经 `generate.mjs --append` 写回 profile patch，**已热生效、无需重启**

<!-- 20261001-015 -->

## `dsh-temp-root` 插件已加 `ensureFull…

`dsh-temp-root` 插件已加 `ensureFullControl`（默认 true）：采纳 temp 根前用 `icacls <root> /grant "<DOMAIN\user>:(OI)(CI)F"` 补当前用户 FullControl（已存在或继承到就跳过；

失败只警告并打印可照抄的命令，**绝不抛异常**——抛了插件会失效、进程退回 `R:\Temp`，比留个可手工修的 ACL 更糟）。

两个手工验收脚本均 PASS：`dsh-temp-root\tests\ensure-full-control.manual.mjs`（纯 Node，造一个「只有 Authenticated Users: Modify」的探测目录）与 `dsh-temp-root\tests\ensure-ace-in-electron.mjs`（app 自带 Electron 44 里对真实 temp 根补 ACE）。

`dsh-temp-root\README.md` 已同步（配置表 + 「为什么还要补一条 ACL」小节）

<!-- 20261001-016 -->

## 5 个旧模式已迁入桌面版（`@deepseek-ai/dsh-a…

5 个旧模式已迁入桌面版（`@deepseek-ai/dsh-agent-preset` 行，追加在 `profiles\desktop\cordis.patch.yml` 里由脚本生成的段落）：`collab` 协作模式 order 10、`plan` 规划模式 11、`introvert` 内向模式 12、`pity` 卖惨模式 13、`slacker` 撂挑子模式 14（`chat` 对话模式是 9）；

live 树里这 5 行全部 `enabled:true, fiberPhase:active`（新增行热生效，不必重启）。

组合以 shipped `standard`（`@deepseek-ai/dsh-web-app@0.2.0-rc.2` 的 `presets/standard.patch.yml`）为模板，persona 从旧 `text: |-` 抽出改写成新版必填的 `prefix: |-`（`{{model}}`/`{{cwd}}` 保留，新版会插值）。

### 更正 012

profile patch 里用户自建的内容现在是 chat + temp-root + spill-local 覆盖 + 这段 5 个预设（其中的 plan 规划模式已于 2026-11-01 归档）

<!-- 20261001-017 -->

## 预设迁移的工具与重跑方式（都在工作区 `dsh-desktop-…

预设迁移的工具与重跑方式（都在工作区 `dsh-desktop-presets\`）：`generate.mjs`（`node generate.mjs [--append]`）从 unpkg 取/缓存 `standard.patch.yml`，把它的 `plugins:` 列表按**顶层行**切片，每个模式只替换 persona 并增删指定行，产出 `generated.patch.yml`；

带 `--append` 时先按标记 `# ── 用户自建预设（本段由 dsh-desktop-presets/generate.mjs 生成…）` 截掉旧段再追加，**幂等**（写 profile patch 在工作区外，需 danger-full-access）。

`inspect-legacy.mjs [ids] [--no-diff]` 是只读诊断：打印旧目录式预设的行清单、persona 原文、与旧版 standard 的逐行差异。

**persona 的源文件现在优先取工作区的 `dsh-desktop-presets\personas\<id>.txt`**（存在即用它、不再从旧目录预设抽取），所以改提示词只动工作区文件 + 重跑脚本即可（`--append` 那一步仍需提权写 patch）；

GUI 卡片文案用 `MODES[].descriptionOverride` 覆盖

<!-- 20261001-018 -->

## 迁移留下的两处已知缺口（都留了处理线索）

①**python 模式未迁**——旧预设引用的 `@deepseek-ai/dsh-tool-python` 在 0.2.0-rc.2 里不存在（app.asar 内 289 个 `@deepseek-ai` 包里没有该包、npm registry 返回 404、checkout 与工作区都没有源码），即无残留可用，用户明确要求先不迁；

日后若有实现，在该预设的 `plugins` 里加 `- id: tool-python` / `name: <实现>` 即可。

②**plan 模式没有 `read`**——0.2.0-rc.2 的 `@deepseek-ai/dsh-tool-fs` 没有只读开关（config 只有 readLimit/readMaxLineLength/readMaxBytes/readStreamMinSize），放开它就同时给 write/edit，所以生成段在 tool-fs 应在的位置留了注释行：取消注释 = 「能读也能写，约束只剩 persona」，不取消 = 该模式只有 glob/grep（GUI 卡片描述已按真实能力改写，不再声称"可读取文件"）
