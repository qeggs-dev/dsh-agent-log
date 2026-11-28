<!-- 20261128-005 -->

## 新增插件「界面重载」ui-restart（2026-11…

**新增插件「界面重载」`ui-restart`（2026-11-28，`〈工作区〉/dsh_plugins/ui-restart`，包 `@local/dsh-ui-restart` 1.0.0，bundle 行 id `ui-restart`，desktop profile 已安装、fiber active，独立 git 仓库，提交 60e0f19 → b0473ec → b9bf00a → 869111d；

quick-restart 提交 2e8573a → ae29b69 → 6ffa04e）**：两个入口共用 Host 的重载广播，目标是让**所有在线 UI**从 DSH 服务器重新加载（`location.reload()`），不重启 App、不重启 Host 插件。

①Quick Restart 页面动作：`dsh-quick-restart` 1.3.0 扩展出 `page: { command: 'reload', endpoint?: '/path' }` 契约（不能与 relaunch/restore/control 同时给，command 目前只有 reload，endpoint 必须是同源绝对路径）；

菜单项显示「重新加载界面」+「不重启 App」角标；点击先 `POST endpoint` 让插件广播，再重载当前页，请求失败或 1.5s 超时仍会重载当前页。②`ui_restart` 工具：`description` 必填（R-005）；非 danger-full-access 会话先审批；

Host SSE `GET /ui-restart/events` 向所有已连接页面（含其它窗口/标签页与局域网镜像页面）广播 `event: reload`，客户端 EventSource 收到后重载；没有页面订阅时直接报错、不弹审批；`POST /ui-restart/reload` 是菜单项的广播端点。

路由优先用 `connection.requestRejection` 准入。

### 实测

`/quick-restart/actions` 返回 ui-restart（order 5, page `{command:'reload', endpoint:'/ui-restart/reload'}`）；菜单点击记录到 endpoint POST 且 `navigationType=reload`；

`ui_restart` 返回「Reload signal sent to 2 open DSH pages」，随后页面 `navigationType=reload`；之后只剩 1 个页面时同样成功。

### 测试

quick-restart 31 项 + ui-restart 27 项全过。UX 评审已做，修复了页面动作失败误报「重启失败」（改用「操作失败」/「Action failed」）、菜单描述重复、审批卡未说明所有页面会重载等；

P3 遗留：菜单入口藏在「重启 DSH」箭头下，`dsh.client.inject` 仍挂着 settings 客户端（未删，保持已验证的加载路径）。
