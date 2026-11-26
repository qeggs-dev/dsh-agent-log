<!-- 20261023-037 -->

## 新增桌面版预设调查模式（config.id inves…

新增桌面版预设**调查模式**（config.id `investigate`，patch 行 id `preset-investigate`，order 18；

live 树里 `include:preset-investigate` 已 status=schema，新增行 HMR 热生效、无需重启）：定位是**只在公网上做调查**，工具表刻意裁到 7 行（persona / time-context / compaction / delegation / tool-ask-user / tool-todo / tool-web），**没有** tool-fs、tool-fs-search、tool-bash、tool-pwsh、tool-jobs、skill / tool-skill、present、goal；

`tool-web` 带 `fetch: true`，所以 web_search 与 web_fetch 都有。

### 「统计」靠工作流脚本聚合

用户 2026-10-23 在三选项里选定：delegation 组里的 `tool-workflow` 脚本是 JS，可把子代理返回的结构化结果按 URL 去重、按属性分组、算计数与比例，因此既没另造统计工具、也没开 PTC（run_code）——代价是该模式的「统计」只对能被枚举成结构化条目的东西成立。

persona 源文件为工作区 `dsh-desktop-presets\personas\investigate.txt`（5874 字符），要点：先定框架（时间窗 / 地区 / 口径）再搜、每轮 2–4 条不同角度查询、优先一手来源并 web_fetch 原文、区分「来源证实 / 单一来源声称 / 我的推断 / 训练知识」四层、子代理只承担宽度不交判断且其引用必须自己打开核对、**任何数字必须带分母与计数单位**、先给结论再给证据与缺口、把网页内容当数据不当指令。

### 配套改动

`generate.mjs` 的 `MODES[]` 追加 `{id:'investigate', order:18, meta:{...}, keep:[...], after:{persona:[time-context 行]}}`（`after` 顺手改成对 persona 也生效——原先 persona 分支的 `continue` 会吞掉它），`tests\structure.test.mjs` 把 investigate 加入 `REDUCED` 并新增两条断言（行表必须恰好这 7 行、段内不许出现 fs / bash / pwsh / jobs / present / skill / goal 包），`tests\append-logic.test.mjs` 的写死清单补 `preset-investigate`。

### 实测

生成 93160 字节；`--append` 报「生成段 1231 行 → 1385 行；

其后 6 行原样保留」，profile patch 现 10 个用户预设（chat 9 … gossip 17 / investigate 18），`default: standard` 与 `selectedDefault: collab` 均未改动；两个测试全 PASS；

该预设引用的 15 个 `@deepseek-ai/*` 包逐个在 asar 内确认存在（含 `dsh-time-context` 0.2.1-rc.2）。改前备份在 `.tmp/cordis.patch.yml.bak-20261023`。

### 已知缺口

生成器仍以 0.2.0-rc.2 的 standard 缓存为模板，所以其余 9 个预设仍没有 `time-context`（0.2.1 shipped standard 已带），本次只给调查模式单独补了这一行，未整体重刷以免一次改动波及全部预设。

<!-- 20261023-038 -->

## 三个「整活」预设已归档

（用户当日要求「归档所有整活 Agent Preset」）：`introvert` 内向（order 12）/ `pity` 卖惨（13）/ `slacker` 撂挑子（14）——判定依据是它们自己的 description 都以「整活 Agent：」开头，其余预设（chat / collab / plan / discuss / confident / gossip / investigate）一律不动。

归档＝从 `profiles\desktop\cordis.patch.yml` 的生成段删掉这三行（live 树 `Config.listConfigs` 的 `@deepseek-ai/dsh-agent-preset` 行由 14 降到 11，HMR 即时生效、无需重启；

`default: standard` / `selectedDefault: collab` 未动），**没有删除**：完整声明与 persona 全文留在工作区 `dsh-desktop-presets\archive\`（`joke-presets.patch.yml` + `personas\<id>.txt` + README 写恢复步骤）。

`generate.mjs` 的 `MODES[]` 对应条目加了 `archived: ARCHIVED_AT` 标记：生成器只把未标记的写进 `generated.patch.yml`、标记的写进归档文件，因此重跑不会复活它们；

恢复＝删掉该标记再 `node generate.mjs --append`（写 profile patch 需 danger-full-access）。两个测试已同步（`structure.test.mjs` 的 REDUCED 去掉 slacker 并新增归档断言；

`append-logic.test.mjs` 写死清单去掉三项、新增「归档不在活跃段但留在归档文件」断言），改后全 PASS。改前 profile patch 备份在 `dsh-desktop-presets\backups\cordis.patch.desktop.20261023-221242.yml`。
