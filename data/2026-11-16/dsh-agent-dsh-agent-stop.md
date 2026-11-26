<!-- 20261116-008 -->

## dsh-agent-stop 插件（0.1.0，2026-11-16 完成、安装并验证）

用户需求「暂停 Agent 循环但不终止本轮会话，给一个开关」+ 明确约束「这是 UI 插件，不能注册 tools」。

### 机制

Host 在 `agent/pre-step` waterfall 里 `await` 一个按 session 的闸门（`gate.js`）；`preStep()` 会 await 该 waterfall，所以挂住等于本轮 turn 保持打开、不发模型请求、不追加事件，放开后从同一步原地继续。

生效时机是**下一个步骤边界**（已开始的模型流与工具批会跑完）。用户点 Stop 仍会 abort turn signal → 闸门释放、本轮按普通 abort 结束，但**不会自动关掉开关**（闩锁；下一条消息会在第一个边界再次被按住，README 已写明）。

状态存 Host 进程内存、按 session、不跨重启；子代理是独立 session，不在范围。Host 端点：`GET /agent-stop/state?session=` 与 `POST /agent-stop/set`（同源 + token）。

Client 在 `conversation.input.left`（order 40）常驻开关，1200ms 轮询；四档文案 暂停/暂停中/已挂起/已暂停，running 读槽位 `useSession(s=>s.running)`。

### 验证

单测 6/6（本会话沙箱默认 `node --test` 会 spawn EPERM，改用 `--test-isolation=none`）；`install_bundle` 返回 application=applied；

### 端到端用临时会话

paused→send→held:1 持续 7.0s→resume released:1→同一 turn 从 turn/start 到 step/start 共 8.69s 被挂住、随后产出「1+1 等于 2。」并 completed；临时会话已归档。

UI 证据：页面 DOM 有 `.dsags-button`（13px/8px、aria-label 含「暂停」），暂停态 token 实测背景 rgb(228,237,253)、文字 rgb(65,118,230)。

### 设计坑

`--dsw-alias-bg-layer-2` 在亮/暗主题都等于输入卡片底色（选中态等于看不见），选中态要用 `--dsw-alias-state-business-tertiary/primary`。

### 未验证

截图/肉眼渲染、多步 turn 每步都停、暂停期间点 Stop 的活体行为（仅单测覆盖）。
