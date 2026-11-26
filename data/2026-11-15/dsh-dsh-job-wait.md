<!-- 20261115-004 -->

## 承 20261114-009

`@local/dsh-job-wait` 改成**统一取消注册表**（用户要求「让其它插件注册取消接口进去，自己只保留适配官方的部分」）。

服务名由 `jobWaitControl` 改为 **`ctx.waitControl`**：`register(provider) → unsubscribe`（provider = `{kind, list(), cancel(id, reason)}`；kind 全 Host 唯一、重复注册抛错；

list 抛错只丢该 provider 的条目）、`active()`（合并所有 provider 的条目并把 `kind` 覆盖成 provider 的 kind）、`cancel(selector, reason)`（选择器 `{id|jobId|sessionId|all}`，可再带 `{kind}` 限定；

返回打断条数）、`providers`（kind 列表）、`agentWaitHooked`。

**本插件只留两段官方适配**，而且它们也走同一接口注册：`job`（包 `jobs.wait`，覆盖 `job_output` 与前台 `pwsh`/`bash`）与 `agent-wait`（包 `wait_agent` 定义、用 `agent.inject` 唤醒）。

### sleep 适配移出

`dsh-tool-sleep` 自己 `ctx.inject(['waitControl'])` 成功后注册 `kind:'sleep'`（没有 hub 时照旧工作，`sleepControl` 接口与钩子不变）。

### HTTP

state 的 `sleepAvailable`/`sleepEvents` 换成 `providers`，cancel 的 `byKind` 按已注册 kind 动态给键，body 可带 `kind`。

### 验证

单测 job-wait 9/9、sleep 12/12（新增 provider 注册/校验/注销、按 kind 过滤、动态 byKind、sleep 侧 provider 委托）；

线上（另一个会话重启后加载）：`providers: ["job","agent-wait","sleep"]`、`agentWaitHooked: true`；

子会话 `sleep(120000)` → `POST /job-wait/cancel {sessionId, kind:'sleep'}` → `byKind {sleep:1}`，**849 ms** 返回「已被插件取消（provider self-test）」，正常返回无报错。

### 另一处变化

工作区重组，本地插件从根目录移到 `D:\Projects\Deepseek_Harness_Workspace\dsh_plugins\<name>`，profile 的 link 已指向新路径。
