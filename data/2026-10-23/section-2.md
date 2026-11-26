<!-- 20261023-031 -->

## 待办（repeater-backend v0.4 之后，见 02…

待办（repeater-backend v0.4 之后，见 029/030/033）：①插件现在**已启用**（设置页需要它；没有 cfg 时它不监听、不建 Session），要关就 `plugin_manager set_bundle false`；

②QQ 侧命令仍是停用名 `_deepseek_harness.py`（改回 `deepseek_harness.py` 即注册），**真实 QQ 的 WS 链路没跑过**（只有离线三帧测试与 HTTP 侧实机验证）；

③`break` / `buffer` 只有形状没有语义（`cancel_count: 0`、恒 404），真取消要对 Session 调 `sessionController.cancel`，且会波及同 Session 的其它调用方；④流式是「每步一条完整消息」而不是逐 token；

⑤实机验证留下两个真实 Session（`.tmp-live` 已删；答案「收到」那条挂在 `〈工作区〉` 下），要清理得在 GUI 里删。
