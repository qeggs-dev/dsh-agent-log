<!-- 20261122-006 -->

## 新增 DSH 桌面插件 @local/approval-in…

新增 DSH 桌面插件 **@local/approval-intercept（审批拦截）**：源目录 `〈工作区〉/dsh_plugins/approval-intercept`（独立 git 仓库，初始提交 6f82ef6），bundle 行 id `approval-intercept`，`install_bundle` → `application: applied`、warnings 空。

### 目的

官方审批卡渲染在发起会话自己的对话列里，用户正在看别的会话（或首页）时卡片没人看、turn 像卡住；会话根本没在页面里打开时请求还会直接 `unavailable` 失败关闭。

### 实现

Host 半在 `approval/request` 上 `prepend` 一个监听，若请求会话不是「主对话正在显示的会话」，就抢下请求并 `ctx.notice.create` 一张 WARN 通知卡（120 秒超时，三个按钮：允许一次 / 拒绝 / 默认卡片）；

允许→`allowed-once`，拒绝→`rejected`，默认卡片/超时/左划/点卡片本体/被挤掉→`next()` 交回官方答案链。

### presence

Client 半（`dsh.client`，无 UI）订阅 `ctx.sessions.list`，把 `retainedBy.mainView > 0` 的会话 id 每 10 秒 POST 到 `/approval-intercept/presence`（进程级 token + Origin 校验，30 秒 TTL）；

没有任何页面心跳时一律交回官方卡片（装在旧页面上也透明降级）。

### 关键取舍

通知卡**不传 sessionId**——传了会让每次按钮反应往该会话 `followup` 一条消息并唤醒新 turn，只传 `sessionTitle` 供显示；子代理会话（`header.origin === 'subagent'`）不拦，交给 subagent-access 的通知流程；

超时/忽略**不移动用户视图**，只有点「默认卡片」或点卡片本体才通过 `/approval-intercept/state` 交接、让客户端 `ctx.get('uiWorkspace').openSession()` 切到该会话。

### 验收

`node scripts/host-harness.mjs` 30 项检查全过（无页面上报、其它会话拦截、允许/拒绝/默认卡片、超时、忽略、abort、子代理跳过、被监视会话放行、隐藏页面、首页、presence 过期、坏 token、外部 Origin）；

真实冒烟——后台会话「审批拦截冒烟测试」（session-083e8869）调用 `request_approval`，审批被拦成通知卡（`/dsh-notice/state` 里标题/正文/三按钮/120s 正确），点「允许一次」后该会话得到 `outcome=approved` 并正常结束，notice 列表清空。

**限制/待办**：新装的 Client 半**要重启 DSH 才会被页面加载**（`install_bundle` 只热加载 Host 半；boot manifest 没有新的 client 模块时页面不会上报 presence），用户选择「我自己稍后重启」；

重启前插件按设计透明降级为官方卡片，重启后需再确认页面出现 `/approval-intercept/presence` 上报，才算 Client 半验收。

**2026-11-23 修正（卡片正文布局）**：用户质疑「描述真的写到卡片上了吗」。

### 查实

描述确实在 notice payload 里，但通知卡正文由 notice 插件渲染成 `maxHeight: 6.2em`（约 4 行）+ `overflowY: auto`（`dsh_plugins/notice/client.js` 的 NoticeCard 内联样式），旧版正文先用中英双段说明打头，把「原因 / Reason」挤到内部滚动区以下，看起来像没写。

### 改为

卡片正文第一行 `描述：<reason>`（第二行只留「点默认卡片交回官方卡片；超时也会退回」），工具名移到标题 `审批请求：<tool>`，会话名/ID 留在页脚（`sessionTitle`，仍不传 `sessionId`）。

用 `notice` 工具按同一标题/正文/三按钮做像素级预览（`screenshots/approval-card-fixed-with-actions.png`）确认描述与三个按钮都在可见区。Host 模块改完仍需重启 DSH 才在真实拦截流程生效；改动提交 42636f2。
