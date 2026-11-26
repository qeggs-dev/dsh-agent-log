<!-- 20261114-031 -->

## 界面端口镜像：扫码后需电脑确认 + 可记住设备

（插件已迁到 `D:\Projects\Deepseek_Harness_Workspace\dsh_plugins\dsh-ui-port-mirror`，独立 git 仓库）。

### 扫码只算「提出连接」

`POST /__mirror/unlock` 现在只创建一枚 pending claim（`Pending`：id/ip/userAgent/createdAt/expiresAt=120s），不再直接发 cookie；

手机端轮询 `GET /__mirror/pending?id=`（1.5 s 一次），电脑设置页「等待确认的设备」列出 IP/UA/时间，允许/拒绝（可勾选「记住这台设备」，默认勾选）→ `POST /ui-port-mirror/pending {id, approve, remember}`；

**第一次 approval 后的轮询**才返回 `set-cookie`（Secure）并一次性下发 remember 材料。

### 记住设备

批准时生成 32B secret，服务端只存 `sha256(secret + ':' + at)` 到 `%DSH_HOME%\plugin-data\dsh-ui-port-mirror\devices.json`，`{secret, at}` 交给设备存 localStorage（key `uipm.remember`）；

下次进 `https://<ip>:8443/` 先 `POST /__mirror/remember {secret, at}`，成功直接进界面、失败清掉本地再回扫码页。会话仍是 2h `uipm_session`，DSH bearer cookie 只在代理内。

**「让所有设备失效」现在同时忘掉所有记住的设备**（`revoke()` 清 devices 并持久化）；关/开镜像、改端口/IP 也会清。侧边栏开关在有 pending 时圆点变警告色、title 带「待确认 N」。

实测 `verify-approval.mjs`：scan→pending 列表 1 条（ip/UA 正确）→未批准时设备只看到壳页→approve+remember→轮询 approved+cookie+remember→app 46228B→第二次轮询不再发材料→remember 登录成功→错 secret 401→deny 后状态 denied→设备列表 1 台；

`verify-gate.mjs` 改为 scan+approve 后全链路（308/壳页/401 重放/HTTPS 首页/404/WSS 101/吊销回壳页/回环 303）全过；`verify-invalidate.mjs` 关开后旧 cookie 回壳页、票据轮换；

页内扫码仍含 `pollClaim`/`tryRemember`/「等待电脑上确认」。

### 注意

pending 的批准界面只在设置页，没开设置页就看不到待确认（侧边栏只有色点提示）；设备列表目前只展示数量与记录，没有单台移除 UI。
