<!-- 20261118-008 -->

## 新增 DSH Host 插件 **子智能体广播**（包 `@lo…

新增 DSH Host 插件 **子智能体广播**（包 `@local/subagent-broadcast`，源码 `D:\Projects\Deepseek_Harness_Workspace\dsh_plugins\subagent-broadcast`，独立 git 仓库，提交 44de070）。

注册工具 `subagent_broadcast`：必填 `description`（≤500 字符单行，审计用途，结果带 Purpose 行）、`message`（≤16000 字符，可多行）、`members`（字符串 "all" 或非空子智能体 session id 数组；

空数组直接拒绝，"all" 不可与 id 混填）。

### 语义

`all` 展开为当前会话树内除调用者外的全部 continuable 子智能体；显式 id 在发送前按 `ctx.subagents.listDescendants(root)` 全量校验（未知 id、调用者自身、one-shot/external 一并报错且不发送），上限 100 个目标；

逐个走 `ctx.subagents.sendMessage` 投递，单个失败继续其余并在 results 里逐目标报告，全成功才 ok=true。

测试 15 条 `node:test`（沙箱内用 `node --test --test-isolation=none` 跑，普通 `--test` 会 spawn EPERM）；

已用 plugin_manager install_bundle 装入 desktop profile（application: applied），实测空列表与空树 "all" 均报错、向真实子智能体按 id 与 "all" 投递均成功（子代理回复 OK）。
