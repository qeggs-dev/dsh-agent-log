<!-- 20261119-005 -->

## **新增 DSH Host 插件「正则路径筛选」`dsh-reg…

**新增 DSH Host 插件「正则路径筛选」`dsh-regex-paths`（2026-11-19，`〈工作区〉/dsh_plugins/dsh-regex-paths`，包 `@local/dsh-regex-paths` 1.0.0，bundle 行 id `regex-paths`，desktop profile 已安装且 fiber 状态 active，独立 git 仓库，提交 9adfbf8 / 00465aa）**：注册工具 `match_paths`，扫描一个目录树，只用一条 JS 正则匹配每个条目的**展开后绝对路径**（统一 `/` 分隔，不含 `./`、`../`、也不含反斜杠），命中的结果**只返回路径列表**，不读文件内容。

用户口径（2026-11-19）：「筛选只返回路径列表」「正则匹配的是展开后的绝对路径（无相对移动符号）」。

### 参数

必填 `description`、`pattern`；可选 `path`（默认会话工作目录，也可指向单个文件）、`includeDirs`、`caseSensitive`、`followSymlinks`、`maxDepth`、`maxResults`、`display`（auto/relative/absolute；

auto = 命中路径在会话工作目录内就给相对写法，否则绝对，绝不输出 `..` 段）。

### 实现

`lib/walk.js` 按目录层 BFS + 有限并发（默认 8）readdir，用 `node:fs` 遍历；根路径优先经 `ctx.fs` `resolve`/`stat` 取规范绝对路径，没有该服务时退回 `node:fs`；

三重预算（命中数 maxResults=200、已扫描条目 maxScannedEntries=20 万、层数 maxDepth=64）加工具超时 30 s，结果用 `stop` 字段说明 `complete|result-limit|scan-limit|depth-limit`；

不可读目录计入 `unreadableDirs`，不炸整次调用。**不做隐式忽略**（node_modules/.git 不自动跳过，要排除就写进正则），刻意如此：筛选规则只有一处真相。工具与参数文案英文，README/locale 中文；图标复用 dsh-opener 鲸标加漏斗徽标。

### 实测

工作区全树 2.4 万条目约 0.9 s；扫 `dsh_plugins` 1666 条目 35 ms；单文件根只算 1 条目；

坏正则返回 `pattern is not a valid regular expression: ...`，缺路径返回 `path does not exist or cannot be read`。

`node --test-isolation=none --test "tests/*.test.mjs"` 17 条全过。

### 打包

`packaging/build.ps1`（先跑单测再 pack）产出 `dist/local-dsh-regex-paths-1.0.0.tgz` 与 `dist/dsh-regex-paths-skill-1.0.0.zip`（SKILL.md + plugin/ 下的同一个 tgz），dist 已 gitignore。

### 注意

安装后改插件源码必须重启 DSH 才会换到新的 JS 模块代，本次改 `display` 规则后就靠一次重启才在本会话生效。
