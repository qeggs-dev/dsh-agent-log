<!-- 20261114-008 -->

## 决策（2026-11-14，用户明确两次）

dsh-ssh 的**登录名（操作系统用户）归属**规则 —— **AI 提案，人决定**。

### 具体

① `ssh_link` 的 `username` 参数仍然是必填（host 形态），AI 想用哪个就传哪个，它就是弹窗里的**预填默认值**；② 弹窗里登录名是**可编辑输入框**，主机/端口只读；

③ 人改过的名字才是实际登录用的、也是被保存进清单与凭据存储的那个（item id 也按改名后的 account 生成）；④ 结果里同时报 `username`（真正连上的）与 `requestedUsername`（AI 申请的，仅当两者不同才出现），并明确写「你批准了不同的登录名，以后按 X 走」；

⑤ 非法登录名（含空格/控制字符/超 64 字符）在握手前就被 400 拒掉，请求保持 pending 可重试。

### 测试

25 端到端 + 17 单元，含一条专测「人改成正确账号后连接成功、清单与凭据都按新名字、错误猜测不会落盘」。 追加（同日，用户指出「AI 填错 host 用户没法改」）：规则从「登录名」扩展到**整套目标** —— 弹窗里 **主机 / 端口 / 登录名三项都可编辑**，AI 给的只是预填值；

`POST /dsh-ssh/answer` 可带 `host`/`port`/`username`，服务端各自校验（host 非空且无空格/控制字符、port 必须 22–65535 的整数、username ≤64 且无空格），改正后的值用于连接、也用于落盘（item id 按改后的目标生成）；

结果里用 `requestedHost`/`requestedPort`/`requestedUsername`（只在与人留下的值不同时出现）对比实际值，渲染成一句「你批准了不同的目标：……（你申请的是 ……）」。客户端三个输入框互不覆盖：轮询只同步 label，不同步用户编辑中的字段；

`ready()` 要求三项都合法。测试 26 端到端（含「改地址+改端口后连上」「非法端口 400 且请求保持 pending」）。

<!-- 20261114-011 -->

## 决策（2026-11-14，用户要求「要做什么事情首先去扫描 r…

决策（2026-11-14，用户要求「要做什么事情首先去扫描 rules 表；这个表里要写好规则内容、关键词、时间和记忆表中对应的索引条目」）：新增 rules 表作为动手前的规则索引。

列：id（R-NNN，永不复用）/ content（自包含、可判定的规则正文）/ keywords（3–8 个，逗号分隔）/ applies_from（规则生效日期，触发器补 applies_from_ts）/ entry_id（指向 entries.id，详情看该条）/ status（active|archived，append-only，禁 DELETE）/ note（出处，如 AGENTS.md 小节）/ sort_order。

视图 v_rules 联表带出条目章节、日期与摘要。

### 用法

任何任务开始先整表扫 SELECT id, content, keywords, applies_from, entry_id FROM rules WHERE status 为 active ORDER BY sort_order（行数少，不要 LIKE 拆），命中关键词按 entry_id 读详情，未命中再按 AGENTS.md 与记忆规范走。

首批 13 条由既有记忆蒸馏，覆盖：先扫 rules 自身、记忆分层读取、记忆 append-only、改表结构同步、工具必带 description、工具文本英文、优先非进程工具（火绒）、测试不用真实数据、设计纪律、第二与第三工作区、.env 规则、dsh-ssh 登录名；每条都有真实 entry_id。

AGENTS.md 已同步：开头新增「第 0 步：先扫 rules 表」、结构速查、写入时机、禁止事项、扩展点与工作区布局。（2026-11-15 修订：rules 的用法改为按任务关键词查询，不再整表读；见 20261115-007）

<!-- 20261114-014 -->

## 决策（2026-11-14，用户要求）

`dsh-ssh` 增加 ①**独立的 `ssh_forget` 工具**（从清单移除一个目标并**连同系统凭据一起删**，理由是「IP 不固定」），`ssh_list` 改成纯只读（原来的 `forget` 参数移除；一个动作用一个工具）；

②**设置页的「SSH 目标」标签页**（`settings.section`，id `ssh-targets`，order 16）：列出目标（id · user@host:port · 认证方式 · 凭据是否还在）与孤儿凭据，两段式删除（点两次），删除同时删凭据。

设置页**不弹审批卡**（那是操作者自己的动作，不是 Agent 发起的），门是 `POST /dsh-ssh/hosts/forget` 的每进程令牌 + Origin 校验；读走 `GET /dsh-ssh/hosts`。

两端共用同一份 `listValue()` / `forgetTarget()`，Agent 工具与设置页看到的是同一份清单与同一份凭据。

`forgetTarget` 的删除顺序仍是「先凭据、后清单项」，并返回 `existed` / `hadCredential` 以便区分「删掉了」与「本来就没有」（设置页据此回 404）。

### 测试

27 端到端（新增设置页路由用例：列清单、错令牌 403、外部 Origin 403、未知项 404、成对删除）+ 17 单元。设置页 UI 由子代理实现并做过无浏览器的冒烟渲染；真机外观未验证。已提交 `ba86708`。
