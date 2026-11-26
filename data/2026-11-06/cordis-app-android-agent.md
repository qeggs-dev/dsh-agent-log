<!-- 20261106-001 -->

## cordis-host **加密与接入层已完成到「协议全通」**…

cordis-host **加密与接入层已完成到「协议全通」**,`node --test` **146 项全绿**,另有 3 个冒烟(`peer-smoke` / `web-smoke` / `e2e-smoke`)全部 PASS。

### 新增模块

`src/proto/ratchet.ts`(PSK 棘轮 `Kₙ=HKDF(Kₙ₋₁, salt=n_c‖n_s, info=epoch)`,方向分离、失步抛 `DesyncError(带 expected/actual)`、保留一格 `previous` 直到 `commit`、根不保留)、`padding.ts`(桶化 256B,`plaintext‖随机填充‖uint16 长度`,超上限原样发)、`channel.ts`(AES-256-GCM,nonce=4B 前缀‖8B 计数器,**GCM nonce 复用会静默毁掉机密性**所以必须带前缀)、`handshake.ts`(明文只走 hello/hello-ack 且只含 epoch+nonce;失败不改状态)、`access.ts`(会话级 open/redeem/close:open 幂等、token 单次、断开后重开换新 token、已连接时拒绝再开)。

信封 **v2** = 签名(覆盖 header‖密文)+ AEAD,**校验顺序 签名→epoch→counter→解密**,且**被拒的帧不推进防重放计数器**。

<!-- 20261106-002 -->

## cordis-host **会话级临时接入已打通**(M1 收尾)

`src/proto/access.ts` 的 ticket 同时带 **URL(授权 token)与 PSK(加密)**,且 **PSK 不在 URL 里**——抓包看到请求行也拿不到密钥;`payload()` 把 `{url, psk, nodeId, publicKey}` 一起交给二维码。

`peer.ts` 新增 `/s/<sessionId>?t=<token>` 路由:`redeem` 成功即把 token 作废并**一次性交出 psk**,随后走 hello/hello-ack 握手 + v2 信封;`connectSession()` 是手机侧客户端,`hello` 里带自己的公钥供对端钉住(公钥可以在明文里,授权来自 QR 里的 PSK)。

### 踩到并修掉的两个真 bug

①客户端把帧发往占位 id `'host'`,而服务端按自己的 nodeId 校验 `to` → 静默丢包、客户端超时(现在 `peerNodeId` 从 payload 里取);②`ReceiveOutcome.reply` 的类型还写着 v1 的 `Envelope`(有 `body`),但运行时回 v2(只有 `sealed`)→ 读 `reply.body` 得 `undefined` 且**不报错**(JSON.stringify 会丢掉 undefined),只有端到端冒烟能发现。

### 验收

`session-access-smoke`(真 socket)与 `web-smoke`(`/api/access` 三态)均 PASS,单测 **150 项全绿**。
