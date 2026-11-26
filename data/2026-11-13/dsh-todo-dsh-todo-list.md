<!-- 20261113-008 -->

## 新增 DSH 插件 @local/dsh-todo-lis…

新增 DSH 插件 **`@local/dsh-todo-list`（TODO 列表）**（源目录 `〈工作区〉/dsh-todo-list`，bundle 行 id `todo-list`，desktop profile，`install_bundle` 返回 `application: applied`、warnings 空，四个工具当场出现在工具表）。

### 四个模型工具

`create_todo`（建表/追加条目，分配 id 并返回）、`list_todo`（列 id/状态/正文/注释，可 `include_completed=false`、`include_notes=false`）、`edit_todo`（按 id 改 content/note/status，空串清注释）、`finish_todo`（按 id 标 completed 并记 completedAt，重复调用幂等）。

id 形如 `T1`，单调分配、不复用不重编号；输入接受 `t3` 与裸 `3`。

**关键设计：不复用 session 日志里的 `todo/write`**（内置 `todo_write` 写的就是它）。

理由是本插件的列表要跨轮次留存，而 `todos` 投影（`packages/todo/tool-todo`）在**每个 `turn/start` 时把状态清成 null**，只能当「这一轮的计划条」；且 `TodoItem` 只有 content/status，放不下注释与 id。

### 存储

`$DSH_HOME/plugin-data/dsh-todo-list/<sessionId>.json`，一会话一文件、临时文件 + rename 原子写、同一会话的读-改-写走 promise 链排队（实测并行 4 次 finish，计数依次 1→2→3→4，不丢条目）。

文件损坏大声失败并给路径（不静默重建覆盖用户以为还在的表）；单条条目坏则丢弃并在结果里带 `store warning`。

### 上限

表 100 条、单次 create 25 条、正文 500 / 注释 4000 / 标题 200 字符。`config.directory` 可覆盖目录。

**验证（2026-11-13）**：22 项单测全过（model 8 + tool 14：id 分配、状态迁移、注释清除、渲染、跨实例持久化、会话隔离、非 agent 调用被拒、并发不丢、损坏文件、坏条目降级、文档形状）；

在真实会话里跑完 create→list→edit→finish→重复 finish，落盘文件与文档形状一致。**坑**：`node --test tests/` 在本机受限令牌下 `spawn EPERM`（测试运行器起子进程要命名管道），必须逐文件 `node tests/xxx.test.mjs` 在主进程内跑。

插件行标题/描述/图标已按 locale + icon.svg 导出且格式校验通过，**界面渲染未验证**（无浏览器控制）。
