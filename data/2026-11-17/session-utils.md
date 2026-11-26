<!-- 20261117-003 -->

## Session Utils 标题支持（2026-11-17）

`session_create` 新增可选 `title`——创建后立即 `sessionController.rename` 写入并固定，作为初始标题（之后的自动标题生成不覆盖）；结果带 `title` 与 `titleApplied`。新增工具 `session_title`（参数 `session_id` + `title` + 可选 `workspace_id`）：对已有会话调用 `sessionController.rename({sessionId, title})`，返回 `{ok, sessionId, title, previousTitle?, seq?}`；`previousTitle` 取日志里最新的 `session/title` 事件（没有再看 projection）；子智能体会话拒绝，非完全权限每次重命名一次审批。实测：create 带 title 返回该标题，session_title 改名返回 previousTitle 与 seq，session_exists 显示新标题。
