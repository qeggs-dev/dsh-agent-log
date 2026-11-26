<!-- 20261104-001 -->

## 新增项目 **Cordis 宿主 App**（暂定目录 `〈工作…

新增项目 **Cordis 宿主 App**（暂定目录 `〈工作区〉/cordis-host/`）：目标是在**一个 Android App 内同时跑三样东西**——Cordis 运行时、终端、Harness 式的自修改 Agent。

### 关键技术事实

DSH 本身就是 Cordis 应用（`app.asar` 内 `import { Context, Service } from 'cordis'`，组合单位是 `cordis.yml` / `cordis.patch.yml` 的 plugin row，有 `cordis:group`、`!!js`、Loader/fiber，出货 preset 里有一个就叫 `cordis`），所以「先实现一个 Cordis」是唯一正确的地基：自修改的难点不是改文件，而是改完旧实例要**干净回收**（fiber/dispose）。

### 已定架构

①两层落盘——只读 seed（从 APK/载荷释放）+ 可写 overlay（agent 的 patch 与插件），软复位＝删 overlay、硬复位＝清 App 数据；

②**索引文件在外层**（`index.json`，不属于任何版本），字段只有 `indexVersion/generation/active/profile`，**只告诉程序如何索引版本、不管版本是什么**；

版本目录自带 `manifest.json`（`entryList`/`requires`/`digest`）自描述；

③**两条 rename 语义不同**：解压用目录 rename（`.tmp → dir`，目标不存在）、应用更新用文件 rename 覆盖索引（POSIX 原子替换），绝不能用「目录 rename 成活跃目录」当切换；

④resolver 是**纯状态函数**，输入只有（磁盘有效版本清单，载荷种子清单），规则「候选唯一则自动、多个则询问、为空则报缺失」——**不做历史判断**（不写 first-run 标记：用户否决了「首次安装 vs 清数据」的区分，因为两者行为本就一致）；

⑤升级＝新目录 staging + 自检 + 用户确认，确认才改索引，选否保留旧索引与 staging 目录。

### 选型

运行时＝随 APK 打包 Node arm64 二进制（放 nativeLibraryDir 规避 W^X；nodejs-mobile 停在 18.17.2 够不上 DSH 的 ≥22.19，本机 Node 24.21）；内核＝复用上游 `cordis` 包、不自写；

UI＝web 客户端 + 槽位（与 DSH 同构，桌面浏览器与 Android WebView 共用一份，不做 Compose）。

### 顺序

M0 解析器+MVP → 难题速验（pty 真交互 / 禁 `!!js` / 坏重载回滚）→ M1 终端 → M2 agent → M3 自修改 → M4 APK。

### 环境

本机无 Android SDK、无 gradle，JDK 18（AGP 要 17/21，建议并装 21），adb 在 `〈本机路径〉`；npm 缓存在沙箱外会 EPERM，需指到工作区内。

<!-- 20261104-003 -->

## Cordis 宿主 App **MVP 已交付并全绿**（`〈工…

Cordis 宿主 App **MVP 已交付并全绿**（`〈工作区〉/cordis-host/`，依赖只有 `cordis@4.0.0-rc.12` + `yaml@2.9.1`，21 项 `node --test --test-isolation=none "test/*.test.ts"` 全过，约 1.0s）。

### 已实现

`src/boot/`（`resolve()` 纯函数 6 态、index 原子写 + `index.prev.json` 回退、整树 sha256 校验、`.tmp → 目录 rename` 的种子释放）、`src/host/`（entry list 解析、装配、装配失败回滚）、`src/main.ts`（CLI：`--seeds` / `--apply` / `--assemble` / `--choose`）。

### 三个难题速验的结论

①**pty 可用**——`node-pty@1.1.0` 的 win32-x64 预编译包直接随包下载（`prebuilds/win32-x64/pty.node`），`probe/pty-probe.mjs` 在真 ConPTY 里拿到 `[tty]=True` 与 `PTY_ECHO_OK`、退出码 0，**不需要本机编译**；

但**受限沙箱内 spawn 一律 EPERM**（`npm install` 的 install-script 与 pty 探针都必须提权跑），与 `id:20261022-003` 同源；

另 npm 11 默认拦截 install scripts，要 `npm install-scripts approve node-pty`。

②**`!!js` 可被可靠拒绝**——但 `yaml` 会把 `!!js` 归一成 `tag:yaml.org,2002:js`，按 `!!` 前缀写检查会漏，必须按裸标签名比对（已修，测试锁住）。

③**坏重载可回滚**——`openComposition()` 在装配失败时回退上一份索引并清理半挂载 fiber（测试断言日志恰为 `['good:on','good:off']`），没有上一份时**不写任何索引**。

**cordis 4.0 与 3.x API 差异大**：`ctx.plugin()` 返回 `Fiber & PromiseLike<Fiber>`，但 **`await` 它不等于「已激活」**——实测一个声明了 `inject` 而无人提供该服务的行会停在 `PENDING`、函数体**根本不执行**，`await` 却照样 resolve，判活必须看 `fiber.state === FiberState.ACTIVE`（`FiberState` 是运行时导出，PENDING=0 / ACTIVE=2）；

`ctx.fiber.dispose()` 释放整棵树、`ctx.registry.size` 可作「零残留」断言。

<!-- 20261104-007 -->

## cordis 4.0.0-rc.12 的三条硬规则（全部实测，探针在 `cordis-host/probe/`）

①**插件的返回值会被当作 effect 校验**——返回 `undefined`/函数（disposable）/Promise/可迭代对象都合法，返回普通对象（哪怕只是 `{hello(){}}` 或类实例）或数字则抛 `TypeError: Invalid effect`；

所以「插件把 session 对象 return 出去」是错的，服务要通过 `ctx.provide(name, value)` 发布、经 `ctx.<name>` 读取。

②**未声明的服务读不到**——直接读会抛 `cannot get property "terminal" without inject`，必须给插件函数加 `plugin.inject = ['terminal']`。

③**声明了却没人提供的依赖 = 静默 PENDING**——该行停在 `PENDING`、函数体不执行、不报错，而 `await fiber` 照样 resolve；宿主必须自己查 `fiber.state`，`assemble()` 已按此改成「装配后校验 ACTIVE，否则报出该行及其未满足的 inject」。

<!-- 20261104-008 -->

## Cordis 宿主 App **M1 第一步已完成**

`src/host/pty.ts`（`PtyFactory` 接缝 + `nodePtyFactory()` 走 `createRequire` 懒加载、`memoryPtyFactory()` 假终端）+ `src/host/terminal.ts`（`ctx.terminal` 注册表 + 一个终端一个 fiber 的 `terminalPlugin`，dispose 即 kill）。

测试增至 **29 项全绿**。

### 真 pty 验收通过

`verify/m1/terminal-real.ts` 在 `〈工作目录〉/cordis-host/run` 里经 `super_workspace_exec` 跑真 pwsh，得到 `exitCode 0 / sawMarker / sawCols`，dispose 后 `registrySize 0`——即「终端服务能驱动真 ConPTY 且不留残留」已被端到端证明；

`node --test` 全部用假终端，不依赖 spawn。

<!-- 20261104-009 -->

## Cordis 宿主 App 的双端互联协议已定稿并落地第一批纯模块

（用户逐条拍板；`src/proto/` 三个模块 + 17 项测试，全套 46 项 `node --test` 全绿）。

### 架构

①**两个对等节点**，能力对等（同一份程序两角色都能当）、角色不对等（server 持上下文与 key，client 持工具与执行）；`change_space` 只换会话的执行端，**不搬文件、不搬日志**（原「打包→解包迁移」方案已作废）。

②**WS 方向固定**：PC 监听、手机出站（因为手机主动扫码），手机因此不需要监听端口/前台服务；而**「会话服务端」角色与 WS 方向正交、按会话可翻**，消息用 `(sessionOwner, sessionId)` 寻址。

③**1:1 是设计原则不是暂时限制**：一对多会让服务端承担投送、客户端变成被投送方，而选 WS 正是为了两端都能主动发。④**key 绝不进 WS**：谁当服务器用谁自己的 key 发模型请求；

QR 只装配对材料（局域网地址+端口+一次性 token（默认 120s 过期、扫一次即废）+发起方公钥，`src/proto/pairing.ts` 的 `PairingServer` 只接受一个对端，第二个直接 `already-paired`）。

⑤**模型可用性属于当前服务端**（不是执行端），所以 `change_space` 预检的对象是「目标设备作为服务器时有哪些 key/模型」。⑥**密钥轮换强制**：三钥状态机 `current/pending/previous`（`src/proto/keys.ts`），ed25519 逐包签名；

验不过不静默丢弃而是回 `key-epoch-mismatch` 让对方重播公告（把原子性换成可自愈）；**旧钥的退役顺序不可颠倒**——必须先 `promotePeerIfPending`（看到对端真的用新钥签过包）再 `retirePrevious`，否则会切断还没切换的对端。

⑦**客户端上报工具 schema**（名字+描述+JSON Schema）由服务端拼进 prompt 上报给模型；因此 **schema 是不可信输入**，按数据处理、定界、限长、首次上报需人工确认。

⑧**字符集（`src/proto/charset.ts`）是减法模型**：网格是 95 个可打印 ASCII，默认全允许、只关掉少数几个，**排除控制字符但保留表意字符**；非 ASCII 另有一个 `keep/strip` 开关（默认 keep，否则中文描述会被清空）；

`strictToken` 只校验不静默改写名字。⑨**字符集配置是配对级、权威在 WS 监听方**（若跟着会话游走，切一次指纹变一次，「工具集变了」会反复误报），两端必须一致，指纹 `cs1:` 取允许集的 sha256 前 16 位。

<!-- 20261104-010 -->

## Cordis 宿主 App 的**字符集设置界面需求**（用户…

Cordis 宿主 App 的**字符集设置界面需求**（用户 2026-11-04 定，UI 待 web 壳起来后实现）：**手机与 PC 是两套布局**——手机上每行格数少、大按钮、整页竖向滚动，且主视图应是「已排除字符列表 + 一个大按钮添加」，而不是让人在 95 格里逐点（横竖屏各一套列数）；

PC 上格数多，按字符映射表的习惯排版（按类别分组：数字/符号/大写/小写，组内按码点升序），支持拖拽连选与键盘输入。**优先级是操作性高于美观**。

### 两边都要有

实时预览（改一个字立刻看到样例描述清洗后的样子）、与对端的一致性指示（一致/不一致 + 同步到对端）、全选/全不选/按类别反选、当前摘要（如 `allowed 92/95, excluded: "\`|"`）。；

**不可见字符一律用 `[<code>]` 形式显示**（空格 `[0x20]`、`[0x09]` TAB、`[0x1B]` ESC，ASCII 用 `0xNN`、更高码位用 `U+XXXX`），这样"谁是谁"一眼可辨——已实现为 `describeChar()` / `displayText()`（纯函数 + 测试），并且**只用于显示**，绝不可进入 payload 或 prompt（否则 `[0x20]` 会变成字面文本）。
