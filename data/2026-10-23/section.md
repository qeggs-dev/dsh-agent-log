<!-- 20261023-027 -->

## 决策（QQBot 旁听）

把 MaiBot 与 qq-bridge 两套「输入多、输出少」机制**合并成一条判定链**，不是二选一。形态是 Repeater 长 Handler（`/chime`，别名「旁听」）：常驻 `wait_message(listen_group=True)` → `asyncio.Queue` → 有界未读缓冲（30，满了丢最旧，来自 qq-bridge）→ 判定链「私聊 → @ → 关键词 → 概率 → MaiBot logistic 打分」→ 合并窗口（安静 6s、被 @ 1.5s，窗口不因新消息延长、@ 会把窗口提前）→ 一次后端调用。**未命中不清空缓冲**，留到下一批一起判（MaiBot 的 `wait` 语义）；阈值 = 开口率锚点表插值 + 冷却 0.10 + 连败 0.05×n（封顶 3 次）。**模型级弃权（[SILENT] / 工具式发言）在 Repeater 无对应物**，因为回复由 `ChatSendMsg` 直接发出、拿不到「模型决定不说」的信号，所以唯一的省话杠杆是「不调用后端」。代码 `repeater_main\commands\chat\chime.py`（IO 与生命周期）+ `chime_core.py`（纯逻辑，只用标准库），离线测试在工作区 `repeater-backend\tests\chime_gate.py`（门控 41 项）与 `chime_loop.py`（桩掉框架跑循环 17 项）。三个必踩的坑：群聊 `Namespace` 带 `user_id`，默认 `wait_message` 只听得见发起命令的那个人，**必须 `listen_group=True`**；**不能对监听 Future 用 `wait_for`**（超时会取消 Future，随后 `ListenerPackage.set_result` 抛 `InvalidStateError`，炸在 `report_message` 里），要用「队列 + 对 `queue.get()` 超时」；退出时**先 `cancel_wait_message_listener`（锁内原子摘除）再取消任务**。

<!-- 20261023-030 -->

## 决策（repeater-backend v0.3，取代 024）

**放弃「复刻 95 条 API」，改成「工作区即服务器 + 全部操作交给 AI」**，理由来自用户当日三条要求：所有操作接到 AI、混合会话、插件必须指定工作区才能工作（后又补充「不需要完全复刻 Repeater 的工具，大部分时候 DSH 自己的工具就够了」）。工作区开关放 `repeater_plugins.cfg` 的 `enabled = true` 而不是插件配置，因为工作区自描述、改文件即起停，且不会出现「配置说开、目录说不开」两个真相源。v0.1 的手写对话引擎（`src/chat/`）与差分夹具已删除，`contract/` 只留作 agent 的接口形状参照；原 Python 服务既不被移植也不被包成子进程。
