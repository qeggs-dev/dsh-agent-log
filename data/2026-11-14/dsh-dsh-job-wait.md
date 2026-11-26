<!-- 20261114-009 -->

## 承 20261112-002/003

DSH 升到 0.2.2-rc.3 后，把「打断等待」扩到核心 `wait_agent`。

### 升级副作用

profile 的 `dsh.profile.bundles` 里 `@local/dsh-job-wait` 被丢了（依赖仍在 package.json），`GET /job-wait/state` 直接 404；

用 `plugin_manager` 的 `set_bundle(enabled:true)` 重新加回即 applied，不需要重装。

### wait_agent 的接缝

工具在 `@deepseek-ai/dsh-tool-subagent-control`，等待是模块私有的（私有 lifetime AbortController + 模块内 waitForInput），没有服务可注入信号。

### 试过两条路

①包装 `ctx.tools.register` 拦注册 —— **无效**，`ctx.tools` 是 cordis Service（proxy），在实例上赋值不生效（读回仍不等于包装函数，且插件不报错），`agentWaitHooked` 会一直是 false；

②按 Agent 作用域取定义 —— **有效**：工具按预设作用域组合，host 全局 view 里没有 wait_agent，但 `ctx.tools.get('wait_agent', agent)`（scope 传 Agent 对象，与 resolve() 里的 view(agent) 同构）能拿到该 Agent 解析到的定义；

插件在 `agent/created` 上逐个 Agent 挂钩（0/150/450ms 三次重试，定时器 unref），挂载时先扫一遍已有 Agent，卸载时还原 execute。

### 打断方式

不伪造 `{timedOut:true}`（会把内部等待留到最长 1 小时，模型还会以为超时又去等），而是走工具自己的唤醒路径 —— `agent.inject({id, role:'user', content:[{type:'text', text:'<wait_interrupted>…'}] , source:{kind:'cordis-host-runner'}})` 往 next-step 投一条备注，wait_agent 立刻返回 `{timedOut:false}`，模型下一步读到这条折叠插件行，知道自己是被用户打断而不是超时。

### 两个新等待工具没接

`terminal_send` / `terminal_close`（`@deepseek-ai/dsh-tool-terminal`，0.2.2 实验终端 bundle）在本 profile **根本没挂载**（Config.listConfigs 查该包返回 0 条 entry）；

即使挂上也没有「只停止观察」的出口 —— terminal_send 的取消语义是 `LocalSendOperation.cancel() → interrupt() → signalForeground('SIGINT')`（会打断前台程序），绕开它直接 settle() 又不清会话的 active，下一次 terminal_send 会报 SEND_ACTIVE；

terminal_close 的等待就是 `terminals.kill()` 等进程树退出，结果只有 closed/already-closing，提前返回必然说谎。

### 验证

单测 11/11（假 jobs / 假 sleepControl / 假 wait_agent 定义，`node --test --test-isolation=none`）；

### 线上端到端

重启后 `state.agentWaitHooked=true`，子会话 `wait_agent(60000)` → 外部 `POST /job-wait/cancel`（byKind {job:0, agentWait:1, sleep:0}）→ **4.8 秒**返回 `{"timedOut":false}` 并收到原文 `<wait_interrupted> The user interrupted this wait_agent call (agent-wait self-test)`，正常返回无报错。

改 Host 源码仍需重启 App（这次为验证重启两次；另一次是 DSH-SSH 会话自己发起的重启，本会话按 restart_notice 确认）。
