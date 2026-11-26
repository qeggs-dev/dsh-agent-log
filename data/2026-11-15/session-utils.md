<!-- 20261115-003 -->

## Session Utils 接口决定（2026-11-15）

`session_send` 只等对方**收到**（消息进入对方 inbox）就返回，不等对方 turn 结束；

结果带 `messageId` 与 `resumed`（目标原本冷启动被恢复时为 true），`delivery=queue|steer` 只决定排下一轮还是插下一个步骤边界，`interrupt` 退化为 `delivery=steer` 的快捷写法。

`session_wait` 与 archive/fork/move 的 `settleBeforeWrite` 会登记 `waiter → target` 等待边，并在阻塞前从目标出发走完整条等待链，发现环（直接互等或 A→B→C→A）就立即报 `Wait cycle: ... would deadlock (A -> B -> C)` 并拒绝，不进入阻塞。

<!-- 20261115-010 -->

## Session Utils 新增 `session_cancel…

Session Utils 新增 `session_cancel_wait`（2026-11-15）：走 `@local/dsh-job-wait` 的统一取消注册表 `ctx.waitControl`（`ctx.inject(['waitControl'])`，只在它挂载时注册；

与 `session_cancel_sleep` 并存，后者只走 sleepControl）。参数 `session_id` / `workspace_id` / `kind`（job|agent-wait|sleep|自定义）/ `reason`；

先 `waitControl.active()` 筛 `sessionId === 目标` 的条目，无命中返回 `cancelled:false` 且不要求授权；

命中则一次提权后 `waitControl.cancel({sessionId, kind?}, reason)`，返回 `cancelledCount` 与命中的 `waits`（kind/id/jobId/requestedMs/elapsedMs）。

### 实测

目标会话前台 `pwsh Start-Sleep 30`（timeout 60000）在 6.5s 被取消，工具提前返回并把命令提升为后台 job（`still running after 60000ms; moved to background job pwsh-…`），turn 继续。

<!-- 20261115-011 -->

## Session Utils 的 `session_wait` 现…

Session Utils 的 `session_wait` 现在会把自己注册进 `dsh-job-wait` 的 `ctx.waitControl`（`kind: "session-wait"`，仅在 hub 存在时）：阻塞期间 `GET /job-wait/state?session=<id>` 的 `waits` 里能看到它，所以本会话工具栏会出现「打断等待」按钮。

点按钮（或别的会话 `session_cancel_wait`）时，取消信号经 `AbortSignal.any` 合进轮询，`session_wait` **正常返回** `cancelled: true` + `cancelReason` + 已提交片段，turn 继续（不抛错、不算 timedOut）。

### 实测

等待中的会话在 8.4s 被 `session_cancel_wait` 取消后回复 `WAIT-CANCELLED`；同一工具对 `kind: sleep` 也生效（取消后回复 `SLOW-DONE`）。
