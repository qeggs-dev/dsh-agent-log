<!-- 20261105-012 -->

## Cordis 宿主 App **互联层第一步已完成（真 sock…

Cordis 宿主 App **互联层第一步已完成（真 socket 两端对话）**：新增 `src/proto/peer.ts` —— `POST /pair` 用二维码 token 换对方公钥（`PairingServer.redeem`，第二个连接得 `already-paired`），`/peer`（WebSocket）每帧一个签名信封交给 `Transport.receive`；

两端密钥来自 `generateKeyMaterial(1)`（keys.ts 新导出），配对成功后 `KeyRotator.adopt` 用它做 `current`，所以**配对后的第一封信封就能验签**（否则会出现"用对端没见过的密钥签名"）。`ws` 只搬字节，语义全在 `Transport`。

**验收** `verify/m1/peer-smoke.ts` 在 `G:\work\cordis-host\run` 跑出 `verdict: PASS`：`pairedWith pc`、token 重放被拒、snapshot 跨网拿到 cursor 2 / 2 条、租约 push 追加成功（cursor 3）、revoke 后 push 得 `push-rejected: stale lease` 且日志游标仍是 3。

测试仍 62 项全绿（`peer.ts` 需要真实端口，冒烟放在 verify 而非单测）。

### 顺带

web 壳加了「配对」页签 —— `GET /api/pair` 用 `qrcode@1.5.4` 生成 SVG（载荷里 host/port 被覆写成 peer 端地址而不是网页地址），新增的检查让 `web-smoke` 也变 PASS；

`scripts/serve.ts` 现在同时起终端、web 壳与 peer（peer 绑 LAN 地址、不用通配）。

<!-- 20261105-015 -->

## cordis-host 的设计正式落在项目里

（用户要求：设计归项目、不归记忆）：`D:\Projects\Deepseek_Harness_Workspace\cordis-host\docs\DESIGN.md` 是该项目设计的唯一权威，内容包括 seed/overlay/index 三层、解析阶梯（二维查表、无 first-run 标记）、两条 rename 语义、与 DSH 的结构兼容（`TerminalBackend` + `ctx.terminals.registerBackend`）、角色正交（WS 监听固定 PC、会话 home 不搬）、1:1 配对与 QR、三钥轮换、信封四道栅栏、会话拉取（seq 归 home、缺口=resync、租约按代）、字符集减法模型、以及「手机永不监听」这条硬约束及其推论（`change_space` = 只换执行端）。

相应流水记忆（`20261104-001/002/007/009/010`、`20261105-012/013/014`）保留为过程记录，**改动设计请改 DESIGN.md，不要只改记忆**。
