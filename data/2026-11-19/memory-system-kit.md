<!-- 20261119-004 -->

## 记忆系统复刻包 memory-system-kit 1.0.0（工作区 `memory-system-kit/`）

用户要求「打包工作区的记忆规则（不是记忆内容），以便其它 DSH 快速复刻我们的记忆系统」。

产物 `dist\memory-system-kit-1.0.0.zip` 145,695 B sha256 5595F2C0477A3E7F63088A78BA07D20E404CBB0B123E10C411E26218A5039AC9，zip 根为 `memory-system-kit\`，32 条目。

### 只含规则与结构

`AGENTS.snippet.md`（AGENTS.md 的「记忆系统（MEMORY.db）」段逐字导出，路径/时区在安装时替换）、`db/schema.sql`+`db/seed.sql`+`db/MEMORY.empty.db`（10 表/13 视图/10 触发器/14 索引，schema_version 4，WAL 空库）、`references/schema.md|customize.md|provenance.md`、`install.py`、`tools/`（memory_db.py 可 scaffold/check/summary/backup/ddl；

export_from_live.py 从活库只读重新导出；verify_structure.py 两套定义漂移检查；smoke.py 行为测试；

build.py 打包）、`SKILL.md`（R-020 的 skill bundle 形态）、`plugins/local-dsh-sqlite-0.1.0.tgz` + `vendor/dsh-sqlite/`。

**不含**任何 entries/rules/entry_tags/attachments/snapshots 与附件文件。

### 结构单一来源

`tools/memory_db.py` 的 TABLE_SPEC/TRIGGERS 是权威，`db/*.sql` 由活库导出，`verify_structure.py --strict` 用归一化后的 DDL 文本 + 种子行逐项比对，本次 `ok: true`（47 对象全等）；

smoke 18 项全过（DELETE 被触发器拒绝、extra.time 偏移 date_ts、touch 刷新 updated_ts、id CHECK、归档保行、8 个视图可查）。

### 无硬编码

install.py 的源工作区路径来自 `references/provenance.md`，pnpm 由 PATH 或 `〈用户目录〉/.dsh/dsh-runtimes` 自动发现（注意 PATH 上的 `pnpm.CMD` 不能被 node 直接执行，必须用 pnpm.mjs）；

build.py 自测把 kit 解压到临时目录、目标工作区换到 kit 内、时区改 +05:30、用假 profile 跑 install + check + 重跑幂等性，全部通过。

**坑**：DSH workspace-write 沙箱里 python 在**新建子目录**下建 SQLite 失败（`unable to open database file`，即使文件已存在；

直接放在已有目录里正常），所以 verify_structure 用系统 TEMP 根下的唯一文件名而不是 mkdtemp 子目录；`sqlite3.executescript` 会忽略 BEGIN/COMMIT，验证器因此自带按引号/注释/触发器体切分的语句切分器。

### 未验证

没有用 tarball 真走 `install_bundle` 装进桌面 profile（会改用户 profile，留给实际复刻时做）。
