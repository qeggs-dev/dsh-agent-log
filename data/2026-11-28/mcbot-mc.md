<!-- 20261128-006 -->

## mcbot 项目（2026-11-28 建立，工作区 mcbot/）

MC 协议机器人，不用模组。两部分——主服务（Node 24/ESM，service/，wasmoon 跑 Lua、ws 包提供事件流、node:http 手写路由、v0 为 Mock 传输；

默认 127.0.0.1:8710，token 在 service/data/token.txt）与管理 WebUI（web/，零依赖静态页，由主服务托管）。契约见 mcbot/CONTRACT.md（HTTP 端点、WS 事件、Lua 原语、bot 状态机）。

### 服务侧实测

无 token 401、带 token 200；建 bot→connect→online 且位置随 tick 变化；坏脚本 400 带行号且不落盘；while true do end 114ms 内变 error 且服务仍响应；

沙箱内 io/os/debug/package/dofile 均为 nil，require 与 coroutine 可用。v0 只有 Mock 传输，v1 接 mineflayer。
