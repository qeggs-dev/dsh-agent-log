<!-- 20261115-005 -->

## 新增插件 dsh-developer-console（包名 @l…

新增插件 dsh-developer-console（包名 @local/dsh-developer-console，目录 〈工作区〉/dsh_plugins/dsh-developer-console，已 git 初始化、5 个提交），提供模型工具 developer_console：把一段 JavaScript 投递到每个已连接的 DSH 页面控制台（页面 DevTools）执行，并按页面回传完成值或异常。

用户明确要求「内容」= 执行 JavaScript 并回传结果、投递给所有在线页面。

权限照 Shell：会话为 danger-full-access 时不问；其余一律经 ctx.approval 一次性批准（只有 allowed-once 放行），拒绝/取消/无审批通道/无 approval 服务都失败即关闭；

审批卡先写目的（description 参数，R-005 必填），再写明「以页面身份运行、不受会话文件沙箱限制」并给前 160 字符+总长的代码预览；无页面连接时直接返回、不弹审批。

### 传输三条路由

GET /dsh-developer-console/events（SSE 投递 job）、POST /result（页面按 job 回传）、GET /status（页数、连接数、lastSeq、lastOrigin、超时配置）。

路由只接受 loopback 与 dsh-app: 来源（校验 Origin 头），防远程站点订阅代码流或伪造结果；Desktop 页面的转发请求不带 Origin，实测放行。

客户端半部分用相对 URL（dsh-app://app 页面由 shell 转发到 Host，实测可行），调用一到就打印 [dsh-developer-console] job-N · 页面标签 → code，求值结束后打印结果对象；

页面标签 = origin+路径+document.title+8 位短 id，便于多页面区分。值渲染上限 8000 字符；标量/JSON/DOM outerHTML/Error 栈分别处理。

### 已知限制

顶层 await 不可用（源码按经典脚本 eval），异步要包成 (async () => {})() 的 Promise，工具会等待其落定；调用之后才打开的页面收不到；死循环会卡死该页面（Host 等待仍按超时结束并在结果里报缺失页数）；无单页过滤。

### 实测

install_bundle 与 remove_bundle+install_bundle 都是 application=applied、热生效无需重启；1 个页面时验证了 round-trip、Promise 拒绝、错误渲染、控制台打印（用临时 console 记录器确认后已还原）。

重装宿主半部分后客户端会因 EventSource readyState=CLOSED 做退避重连并自动恢复（已实测）。
