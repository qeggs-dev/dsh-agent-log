<!-- 20261118-010 -->

## 用户要求（2026-11-18，原话「不要以审批为准，应该以权限…

用户要求（2026-11-18，原话「不要以审批为准，应该以权限为准，因为 full-access 的时候，审批是 never 的」）：dsh-ssh 的动作授权改为「先看会话权限，再看审批」。

### 实现

index.js 增加 sessionMode / hasFullAccess / approvalBlocked；

requireApproval 在 sandboxPolicy.resolve({session}).mode === 'danger-full-access' 时直接返回，不调用 ctx.approval；

低于 full-access 仍走 allowed-once，策略 never 时保留「本会话关闭了审批」的明确报错（不冒充用户拒绝）。ssh_link 弹窗仍是填参表单、照常出现；full-access 下 pending 与结果不再带 approvalsDisabled 警告。

### 覆盖动作

ssh_shell、ssh_file、ssh_read、ssh_edit、ssh_write、ssh_copy、ssh_tunnel、ssh_session、ssh_forget。版本 0.4.1，提交 50c4851；

新增一条 full-access 端到端测试（approvalPolicy never + approvalOutcome rejected，shell/upload/read/write 全跑通且 approvals.length=0），全量 247 项全绿。

README 增「授权：先看权限，再看审批」，locale 同步。可推广到同类自建插件：需要用户确认的动作先查 sandboxPolicy，full-access 视为已授权，服务缺失时按 workspace-write 保守处理，凭据弹窗不受影响。

 已于 2026-11-18 09:31 重启，0.4.1 已装，/dsh-ssh/token 与 /dsh-ssh/hostkeys 均 200。
