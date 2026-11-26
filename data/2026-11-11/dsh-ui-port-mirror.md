<!-- 20261110-009 -->

## 点「刷新二维码」后面板显示「已停止/未监听」的 bug

不是真的停了——`POST /ui-port-mirror/ticket` 只返回 `{ticket, expiresAt}`，而设置页的 `postSettings` 把响应**整体当成 state**（`setState(payload)`），于是 `enabled/listening` 变成 undefined，UI 翻成停止态；

实际监听器好好的（`/state` 仍 `enabled:true, listening:true`）。

### 修法两处

①host 的 ticket 路由返回 `{ ...describe(runtime), ticket, expiresAt }`（state 字段在前）；

②client 的 `postSettings` 只在该 payload `looksLikeState()` 时才 `setState`，之后无论成败都再 `fetchState()` 一次兜底。

### 教训

设置页所有“动作型”POST 的响应要么整体是 state，要么前端必须做形状校验——否则一个只返回动作结果的路由就会把整页状态打坏。

<!-- 20261110-010 -->

## 壳的脱敏活跃度上报 + 空闲关会话

（用户要求「监听操作频次、仅上报已按下；关会话前问壳有没有正在点的操作；一直有非控制帧流量就不关」）：实现走 **SSE 反向下行 + POST 上行**（不引入 WS 帧层）。

局域网页面由 `rewriteHtml` 注入 `/__mirror/assets/presence.js`，它只统计 `pointerdown/keydown/touchstart` 的**次数**（每 5 秒 POST `{count}`，无任何键值/坐标/文本），收到 `{type:'probe',id}` 只回 `{probe:id,pressed:boolean}`（最近 1.5 秒有没有按）。

服务端 `sweepIdle` 每 20 秒跑一次：`now - max(lastSeen, lastUserInputAt) >= idleMinutes`（默认 15，配置项）时调 `probePresence`（写 probe 帧，1.5 秒超时视为 false），仍未活动就 `gate.closeSession(session,'idle')` → 给该会话的 SSE 流写 `{type:'closed',reason}` 再 end，页面收到后 `location.replace('/')` 回扫码页。

### 关键点

presence 的 GET(SSE) 与 POST 都用 `gate.peekSession()`（校验 cookie 但不刷新 lastSeen），所以只挂心跳的标签页仍会超时；真实请求走 `sessionFrom()` 照常刷新 lastSeen，因此持续流量不会被关。

会话对象新增 `lastUserInputAt`/`streams`；`revoke()` 改为逐个 `closeSession(s,'revoked')`，先通知流再删。

实测（`verify-presence.mjs`，idleMinutes 临时设 1）：index 注入脚本 true、无 cookie 的 presence 401、SSE 200、**71 秒**后收到 `{type:'probe',id:1}`，测试端回 `pressed:false` → 立刻 `{type:'closed',reason:'idle'}`，旧 cookie 再访问得到扫码壳页。

<!-- 20261111-001 -->

## 镜像关开失效 + 断开灰屏

①`applySettings` 里只要监听参数变了（enabled/port/httpsPort/host）就先 `gate.revoke(next.enabled ? 'restarted' : 'disabled')` 再起监听——关闭、重开、换端口、换 IP 都会作废全部会话与未用票据（`revoke(reason)` 现在接受原因，`closeSession` 会先把 `{type:'closed',reason}` 写给该会话所有 presence 流再 end）。

②`vendor/presence.js` 重写：会话被关或 SSE 连续 8 秒连不回来时，往 `document.body` 插一层 `position:fixed` 遮罩（`rgba(12,14,17,.62)` + `backdrop-filter:grayscale(.85) blur(1.5px)`），中间卡片显示「连接已断开」+ 具体原因（idle/revoked/restarted/disabled 映射成中文）+「重新扫码」（`location.replace('/')`）；

`onopen` 时若没被判定结束就自动收起遮罩。

### 实测

`verify-invalidate.mjs` → 解锁后拿到 app 页（43845 B），`enabled:false` 再 `true` 后同一 cookie 变 shell、pair-link 票据已轮换、重新扫码又能进；

`verify-veil.mjs` → 资产含「连接已断开/重新扫码/grayscale」与四种 reason，开 SSE 后点「让所有设备失效」，**4 ms** 内收到 `{type:'closed',reason:'revoked'}`。

<!-- 20261111-004 -->

## 扫码页的镜头变焦（不是二维码铺满）

用户要的是「双击放大画面让二维码更好识别」。

`shellPage()` 的扫描器现在有 `zoom=1 / maxZoom=3` 与 `lastTap` 双击判定（350 ms，绑在 `#stage` 上）：双击把 `video` 用 `transform: scale(zoom)` 放大（`.stage{overflow:hidden}` 裁切），**同时 `tick()` 改为中心裁剪绘制**——`canvas` 尺寸取 `round(vw/zoom) × round(vh/zoom)`，从 `(vw-cw)/2,(vh-ch)/2` 取源，按原分辨率送 jsQR，所以「看到的放大」和「解码的像素」一致；

再双击回到 1×，停止/重启摄像头也会复位。状态栏显示「已放大 3×，双击画面还原。」。

**先做过一版把设置页二维码铺满整屏的遮罩，被用户否掉**（`而不是铺满`），已整体回退（client.js 里 `qrZoom`/`qrZoomHint`/`qrZoomClose`/`data-uipm-qr-zoom` 全部删除，`verify-client.mjs` 指针同步移除）。

实测 `verify-scanner.mjs`：壳页含 `maxZoom`/`toggleZoom`/`onPreviewTap`/`已放大` 与 `stage.style.display = 'block'`，资产 200。

<!-- 20261111-005 -->

## 快速重启 + 提权（两个桌面插件，已装机并实测）

`dsh-quick-restart` 1.1.0 改成「重启动作注册表」——插件 `ctx.quickRestart.register({ id, order, label, description, plainLabel, active, relaunch, restore })`，其中 label/description/plainLabel/active/available 均可为回调：sys-access 注册两个动作——`sys-keep`「保持当前权限重启」（仅提权时出现，直接继承当前令牌、不重新提权）与 `sys-access`「以更高权限重启」/已提权时「重新提权重启」（重新走提权启动）；

普通重启项在提权时显示「回到默认权限」；框架只负责存储/排序/渲染 `/quick-restart/actions`、按 mode 调 relaunch、普通重启按序跑 restore，不含任何权限判断；

`restart_dsh` 的 `resume` 留在顶层，`control` 是「插件字段字典」：键由动作的 `control.key` 给、值必须是插件提供的 object schema（提权插件贡献 `sys_access`，里面 `mode` 是 `elevate`/`keep` 枚举），schema 随注册表动态重建并按 `available()` 过滤，框架不再知道 `sys_access` 这类名字。

关 App 之前先起 relay 并等 ready 文件，提权被取消则 App 不关。

`dsh-sys-access` 负责提权/降级：Windows 提权用 PowerShell `Start-Process -Verb RunAs` 起一个生成的启动脚本（脚本里显式设 `ELECTRON_RUN_AS_NODE=1`/`DSH_SYS_ACCESS=1`，因为提权进程不可靠地继承环境），降级用**中权限看门狗**（提权前由仍普通的 Host spawn 的 detached node 进程，等信号文件后以普通令牌启动 App 并退出；

非提权 Host 启动时清理、24h 无信号自动退）。

### 四条 Windows 实测坑

①Node `detached:true` 时 PowerShell 会静默 exit 0 且 `-Command` 不执行（提权/降级包装进程必须 `detached:false`，且 relay 要等它退出再退，否则关控制台会杀掉它）；

②UAC 的 linked token 是 Identification 级，`CreateProcessAsUser`/`DuplicateTokenEx` 一律 1346，不能用它启动进程；

③`GetTokenInformation(TokenLinkedToken)` 的 `out IntPtr` 拿到就是句柄，不能再 `Marshal.ReadIntPtr`（AccessViolation 崩掉 PowerShell）；

④本机无 Explorer，计划任务 `/RL LIMITED /IT` 能起 Medium 进程但任务实例结束会回收进程树。macOS/Linux 只实现未实跑（osascript/pkexec + uid/gid + chown 清理）。

### 测试

quick-restart 29 项 + sys-access 11 项全过。
