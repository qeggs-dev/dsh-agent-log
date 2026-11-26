<!-- 20261119-006 -->

## `trash` 增加 `path_pattern`（正则批量删除）与 `dry_run`（预演）

（`dsh_plugins/take-out-trash`，commit `2f4b822` / `70ff6b2` / `51eb622`，已重启并在真实工作区实测）。

**语义**：`paths` 与 `path_pattern` 是**并集**（用户逐字要求），留一即可；同一路径两边都命中只算一项（先 `paths` 后模式命中，再在 `inspectTargets` 按展开后绝对路径去重）。`path_pattern` **匹配展开后的绝对路径**（用户逐字要求「展开后的绝对路径（无相对移动符号）」），不区分大小写，原生分隔符。命中目录整棵移动且不再下探。`dry_run: true` 只解析不审批不动盘，条目状态为 `matched`。

**关键实现（踩过的坑）**：①错第一版匹配相对路径；改绝对后 **`\.log$` 会扫整个工作区——本工作区实测 > 200000 条目、光枚举就 112 秒**，直接撞上限。解法是 `literalPrefixOf()` 抽正则开头的字面量、`scanRootOf()` 把它解析成工作区内真实目录作为扫描起点（开头的 `^` 不消耗字符要先跳过，否则前缀变空——这是第二个坑）。②上限改为匹配 200 / 访问 100000 条目 / 45 秒，任一超限在**删除前**报错，一项都不动。③链接（junction）先 `realpath`，真实路径出工作区则计入 `skipped` 且不下探。

**实测（2026-11-19）**：锚定 `^D:\\...\\trash-pattern-test\\` 预演命中 3 项；`[.]log$` 加锚点命中 2 个 .log；真实删除只动 .log，`.txt` 未动，回收站 `$I` 两条且 `$R` 存在；并集预演（`paths` + 模式）命中 2 项且去重正确；无锚定模式在重启后报 100000 上限并给出“以字面绝对目录开头”的提示。24 项单测全过。

**调用方注意**：参数值就是正则源码，**不要再额外 JSON 转义**——直接在参数里写 `\\` 表示一个分隔符（本次因为多写了一层转义，前缀变成 `D:\\\\Projects…`，结果匹配 0 项，白跑一轮）；点号建议写 `[.]` 而不是 `\.`，避免和转义层数纠缠。

**清理**：测试条目已从回收站删除（经 super_workspace 完全权限），`trash-pattern-test/`、`.tmp/pattern-check`、`.tmp/placeholder.txt` 均已清除。

<!-- 20261119-007 -->

## `trash` 再加 `base_path`：模式只扫该目录，默认会话工作区；`base_path` 不在工作区时要审批

（用户 2026-11-19 逐字要求，`dsh_plugins/take-out-trash`，commit `07710a0`，已重启并实测）。

**语义**：`path_pattern` 匹配的仍是**展开后绝对路径**，但**扫描范围改为 `base_path`**（之前固定在整个工作区）；省略 `base_path` 时就是会话工作区，保持旧行为。`base_path` 可以是绝对路径或相对于工作区，必须存在且是目录；只对 `path_pattern` 有意义，单独给会报错（不静默忽略）。扫描绝不离 `base_path`：链接真实路径超出该目录就计入 `skipped` 并跳过。`paths` 不受 `base_path` 限制，两者仍并集。

**越界审批**：`base_path` 不在工作区（严格路径包含判定）时 `approvalPlan` 带 `baseOutside: true`，非 `danger-full-access` 会话要审批且卡片写明 `base_path`。实际判定仍基于“有东西要移”，零命中时不弹卡。

**这一版解决了上一版的核心痛点**：早前因为模式要扫整个工作区、而本工作区 >20 万条目（光枚举 112 秒），无锚定模式完全不可用，只能靠“字面绝对目录前缀”缩小扫描。现在 `base_path` + `[.]log$` 直接只扫那一棵，秒回；字面前缀优化仍在（仅当它位于 `base_path` 之内时生效）。

**实测（2026-11-19）**：`base_path: .tmp/base-check` + `[.]log$` 预演 2 项、真删 2 项且 `.txt` 未动；工作区外 `base_path: D:\Projects\DSH_Normal_Workspace\take-out-trash-base` 预演 1 项且标“outside the workspace”，真调用**确实弹出审批**（会话日志 `approval/asked` + `approval/decided=allowed-once`，reason 含 `pattern /[.]log$/i in base_path …`）；27 项单测全过。测试条目已从回收站清除，临时目录（工作区内外）均已删除。

**验证手法备用**：会话日志是 `session.v4.jsonl.zstd`，用 Node 24 的 `zlib.zstdDecompressSync` 解压后即可 grep `approval/asked` / `approval/decided`，比看 UI 更可靠。
