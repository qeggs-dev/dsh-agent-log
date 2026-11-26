<!-- 20261124-001 -->

## dsh-sqlite 0.2.0 新增第七个工具 `sqlite…

dsh-sqlite 0.2.0 新增第七个工具 `sqlite_script`（文件级操作，路径受沙箱约束，读上限 8 MiB、写上限 32 MiB）：`apply` 应用 .sql 脚本（与 sqlite_exec 同规则：默认单事务、ATTACH/VACUUM INTO/writable_schema/PRAGMA foreign_keys= 一律拒绝）、`dump` 导出 schema/data/all 为 .sql（文件头带 PRAGMA defer_foreign_keys=ON + BEGIN，可原样 apply 到新库；

虚拟表不导数据行）、`export` 把单条 SELECT 写 CSV/JSON（格式按扩展名或 format；BLOB 在 CSV 用 base64、JSON 用 $blob；

重复列名 a/a_2）、`import` 把 JSON 数组按对象键插入已存在的表（一个事务、布尔转 0/1、嵌套值转 JSON 文本、默认上限 10 万行）。`sqlite_admin` 增加 `foreign_key_check` 操作。

实现上把 sqlite_exec 的执行逻辑抽成 runSql(conn, sql, { config, params }) 复用，assertScriptAllowed 统一拦截禁语句。

测试 52 项全绿（新增 apply 回滚、dump→apply 还原、CSV/JSON 导出、JSON 导入、沙箱与禁语句、foreign_key_check）。

### 实机验收

schema.sql 应用 4 statements/changes=4；dump 699 bytes/2 表/4 行；apply 到 copy.db 9 statements；JSON import 2 行；CSV 中文正常。
