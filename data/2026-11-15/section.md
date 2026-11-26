<!-- 20261115-002 -->

## 决策（2026-11-15，用户要求）

新增 DSH 插件 @local/dsh-sub-agent-tree（工作区 dsh_plugins/dsh-sub-agent-tree，独立 git 仓库），把子代理组织成一棵可编辑的树。

架构定为「自维护树结构 + 映射到官方 subagent 执行」：树由插件 sidecar 存（trees/<treeId>/ops.jsonl 只追加且每条带逆操作 + tree.json 原子快照），节点是官方 subagent —— 我们生成 childId，走 ctx.subagents.startActivation({provider:spawn, childId, parent:恒为 root 会话的活 Agent, delivery:caller, label:空串})，因此对话标签直接复用官方 dsh-resource://subagentchat/session/<child>?parent=<root>&mode=continuable，不需要 import 任何 client 包。

官方那层永远是扁平列表（parent 恒为 root），拖拽改父只在 sidecar 生效，这是刻意设计不是缺陷。

### 硬规则

节点必须先写大纲（goal/scope/split/contract/facts/done 六段）才有资格当父节点，该不变量由 tree_delegate 的签名保证（想派生就必须交出大纲）。并入 = 合并两个任务，必须由目标父接受（可同时提交自己大纲的新版本，边变更与新大纲原子提交）；

被并入节点通过 agent.inject 收到新父大纲，落成一条 context 行（source.kind ≠ user 才不渲染成用户气泡）。停止 = 官方 Stop（interrupt，keepInbox），不引入 paused 状态。

UI 是右侧栏 tab type（ctx.sidebarRightTabs.register + sidebar.right.pane.tab），画布支持滚轮缩放（指针为锚）、空白拖平移、Ctrl+空白拖框选、Ctrl+点加选，布局自动不做自由摆放。

### 工具七个

tree_delegate / tree_modifies_outline / tree_subagent_accept / tree_send / tree_broadcast / tree_cancel / tree_status，均必填 description。

概念稿与实现大纲在 dsh_plugins/dsh-sub-agent-tree/docs/CONCEPT.md 与 OUTLINE.md。

<!-- 20261115-007 -->

## 决策修订（2026-11-15，用户要求「修改 AGENTS.md 指令要求

需要按照用户给出的任务进行查询规则，而不是把整个表都读出来」）：rules 的读取方式由「任务开始整表扫」改为「任务驱动的条件查询」。

### 做法

先从当前任务取 3–8 个检索词（专有名词 / 动作词 / 约束词，中英文同义各一），用一次带条件查询 SELECT id, content, keywords, applies_from, entry_id, note FROM rules WHERE status='active' AND (keywords LIKE '%词%' OR content LIKE '%词%' …) ORDER BY sort_order，只取相关行；

命中按 entry_id 读详情，命中多条都要读。0 行时换更宽的领域词重查一次，仍空表示没有直接相关规则，继续按 AGENTS.md 与记忆规范执行，而不是跳过约束。仅跨领域任务、生僻专有名词或拿不准时才兜底：只取 id, keywords 两列挑 1–3 个候选再读正文。

禁止把 SELECT * FROM rules / SELECT * FROM v_rules 当日常路径。

### 配套要求

rules.keywords 是被检索的字段，新规则必须写成下一次同类任务能命中的词（一个领域通用词 + 具体项目 / 工具名 + 中英文同义词），写窄了就 UPDATE 补。

AGENTS.md 已同步三处：第 0 步整节重写（标题改为「按任务查 rules 表」）、其它常用查询里的 v_rules 行改为提示、禁止事项改为「按任务查 + 不为保险整表拉」。本条取代 20261114-011 中「整表扫」的用法。

<!-- 20261115-009 -->

## 决策/进展（2026-11-15，用户要求「dsh-ssh 的功…

决策/进展（2026-11-15，用户要求「dsh-ssh 的功能最好尽量多加一些」）：把 dsh-ssh 从 5 个工具扩到 16 个（提交 38b0a50 传输模块、47e4370 接线+UI+文档、947acce ssh_write，版本 0.4.0）。

### 新工具

ssh_ls/ssh_read/ssh_edit/ssh_write/ssh_copy（SFTP 远端文件）、ssh_shell background + ssh_job output/kill/list（后台长任务）、ssh_session（常驻 PTY，open/send/close/list）、ssh_tunnel（本地转发 open/close/list）、ssh_connections、ssh_hostkeys、ssh_audit；

ssh_file 增加 recursive/resume/maxBytes/mode；ssh_link 增加 via（已保存目标作跳板机）。

### 安全基线

主机密钥 TOFU（known-hosts.json，tofu/strict/off；只在握手成功后 pin；变更时阻断，弹窗并列指纹要人点「信任新指纹并重新连接」才换 pin；item 形态变更直接失败）；审计 audit.jsonl（每动作一行，含目标/用途/结果/耗时/详情，无凭据，2MiB 轮转 .1；

ssh_audit 与设置页可读）。

### 审批

ssh_ls 只读免卡；ssh_read 默认审批（approveRemoteReads:false 可关）；写/上传/编辑/复制/隧道/命令/PTY 每步审批；后台任务 output/kill/list 免审批（start 已审）。

### 传输语义

bytes=本次实际写入（续传为尾部），resumedFrom=起点，目标更大报错，树 2000 文件/512MiB，符号链接默认跳过，无哈希校验。隧道默认 127.0.0.1，宽绑定在卡上标 EXPOSED；与连接同生共死。

PTY 行式、无 TUI/stdin、超时后远端命令可能仍在跑、需要 POSIX shell、最多 8 个。

### 客户端

设置页新增 审计日志(id ssh-audit,17)/主机密钥(id ssh-hostkeys,18)，弹窗加指纹变更面板。

### 测试

9 个文件 244 项全绿（unit18/hostkeys16/audit18/jobs18/remote-fs38/transfer62/pty27/tunnel13/live34）；假服务器新增 PTY shell、direct-tcpip、SETSTAT。

**重启已完成（2026-11-15）**：重启后 /dsh-ssh/token、/dsh-ssh/hostkeys、/dsh-ssh/audit、/dsh-ssh/hosts 全部 200，ssh_hostkeys / ssh_audit 两个新工具在会话里实测可用，244 项测试复跑仍全绿。

### 仍未做

真实主机复验新功能（连接 / 命令 / PTY / 隧道）、弹窗与设置页像素级外观、strict 策略首次 pin 的 UI 入口（需先用 tofu 连一次或手改 JSON）。 【2026-11-18 修订】授权改为先看权限：danger-full-access 不调用审批、直接执行；

低于 full-access 才逐步审批。见 20261118-010 与规则 R-035。
