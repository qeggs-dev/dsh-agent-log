<!-- 20261124-008 -->

## 项目定义（2026-11-24，用户口述；取代 20261124…

项目定义（2026-11-24，用户口述；取代 20261124-005 的「把 DSH 搬上手机」，也修正 20261124-007 的待定）：做一个类似 DSH 的手机 Agent App，但针对手机 API 与权限模型做特化。与 DSH 最大的不同：**没有会话概念，只有代理树**。

一个母代理负责用户对接、分配任务，用一个可压缩的上下文处理所有用户请求；一级子代理负责拆解任务并下派给二级子代理；树至少三层。每个子代理创建后有自己的 Memory 空间（一个 SQLite 数据库文件）和对应上下文（可压缩）。

保留 DSH 式的自修改/插件、工具调用+审批、长期记忆、终端与文件、界面交互（用户多选确认）。

### 用户当前阶段明确

先把产品形态聊清楚，不写代码。

### 待定

母代理并发模型、节点记忆可见性、树对用户的可见程度、审批路由、深度策略、首批手机 API。

### 可复用资产

cordis-host（Cordis 内核 + 真 pty + Web 壳 + 加密配对，M1）；dsh_plugins/dsh-sub-agent-tree（DSH 上的树形子代理编辑器，验证过树 UI、节点大纲与合并语义）；Node 24.22.3 在 Android 15 可运行（20261124-006）。

<!-- 20261124-009 -->

## 设计进展（2026-11-24，用户逐条确认，承 20261124-008）

①通信 = 全双工 actor mailbox，消息类型 assign / steer / ask / report / cancel，全部异步非阻塞（目标忙就排队，steer 可选打断当前步骤）；另有 notice 旁路：任意节点→用户，带来源/类型/动作，用户回应直接回到该节点，根拿一份低成本摘要；

②生命周期 = 默认 ephemeral，可被提升为常驻（保留 memory DB 与角色定义，会话日志归档但不丢）；③记忆 = 私有 + 回报（v1），父不读子全文；④UI = 默认只看母代理的连续对话，可展开指挥台看树/节点/记忆/插话；

⑤派生 = 预算制（每任务带 token/时间/节点数预算，母代理在预算内自由派生，超了找用户批），深度上限 3、宽度上限 N、默认不派生；⑥审批 = 能力在 assign 时授予（spawn-time capability），越界才沿监督链上报到根、用户批，子节点不直接弹审批卡；

⑦第一批手机能力 = 相机/相册、通知、文件（SAF）、位置、终端/命令；未选分享入口/日历通讯录/麦克风语音；⑧仍待定：技术底座（Cordis+Node+WebView 还是原生）、首个验收场景、每节点 memory schema、Android 后台保活与前台服务类型、自修改的边界。

<!-- 20261124-010 -->

## 追加（2026-11-24）

①树深度改为运行时可调的预算资源，不是固定 schema：assign 携带 remainingDepth；>0 才有 spawn 能力，=0 时从工具集直接移除 spawn 并切 solo 提示词；派生时子节点拿 remainingDepth-1；

steer 可运行时延长或收回（收回只禁新派生，不取消已有子节点，cancel 是另一个动作）；节点在 0 深度认为必须拆解时可 ask 父要深度；指挥台显示并可覆盖；另需 maxChildren 防横向爆炸。

②技术底座定了：Cordis + Node + WebView（复用 cordis-host），不做原生 Kotlin、不做全原生。③首个验收场景仍未定；用户选择「继续聊，先不冻」，不冻结 v0。

<!-- 20261124-011 -->

## 结构约束（2026-11-24，用户口述，承 20261124-010）

①母代理与子代理结构完全一样，共用同一个 Agent 基类，只是创建时的初始化参数不同；②应用打开默认打开根节点的会话页面，会话页面也是继承来的同一份内容；③根节点不指定 prompt，使用系统默认 prompt；派生必须写 prompt；④Skill 池全局共享（与每节点私有 memory 相对）。

我提出的待确认结构：AgentInit = {id, parentId?, prompt?, capabilities, budget, remainingDepth, maxChildren, model?, skillPool(global), memoryPath, sessionPath}；

prompt 分三层（系统默认 prompt = 产品人格 + 通用 agent 协议；运行时上下文 = nodeId/parent/剩余深度/能力/预算/skill 池/记忆路径；角色 prompt = 仅子节点，父在 spawn 时写）；

assign 拆成 role/goal/constraints/deliverable/memoryPolicy/reportFormat 结构化字段再拼 prompt；skill 读免费、写要版本化 + 审批 + provenance；共享会话页要求消息 provenance 一等字段；

root 的 session log 需分段滚动。

### 待定

子代理 prompt 是否允许自改。

<!-- 20261124-012 -->

## 追加（2026-11-24，承 20261124-011）

①每个 Agent 的 log 是一个目录，按每 1 万条轮换一个新文件；文件数 >100 时把前 80% 压到一个 zip。

我补的建议（待确认）：双阈值 1 万条或 32MB、大负载外置到 artifacts 只留引用、manifest 记每个 segment 的 seq/字节/状态/所属 zip、压缩做成低优先级可恢复的原子作业（临时 zip→校验→改名→更新 manifest→才删原件）、最近未压缩段直接扫而 zip 只按需解压搜。

②子代理 prompt 创建后不可修改（避免上下文与提示词冲突），只能通过上下文注入插入内容。③母代理通过加载 Skill 了解如何派生子代理；改为提示词使用预设、母代理的内容作为消息注入。

### 我上升为规则

Prompt = 不可变预设（presetId + version），一切动态内容都是带 provenance 的消息；skill 通过 load_skill 工具结果注入；spawn 工具做 schema 校验（skill 教、tool 卡）；

运行中的 agent 钉住 preset 版本，自修改只改库不改实例（实例与定义分离）。④待定：谁能写预设库（用户/设置页、母代理提议+用户批、任意 agent 可写但版本化）。

<!-- 20261124-013 -->

## Skill 池改为栈帧 / 词法作用域（2026-11-24，用…

Skill 池改为栈帧 / 词法作用域（2026-11-24，用户口述，承 20261124-012）：下层对 Skill 的改动默认不影响上层；子代理创建的 Skill 只能同级加载访问；只有子代理执行「修改」时，程序才会拿到上层的引用，从而修改那片 Skill；Skill 修改需要审批。

### 我形式化为

节点可读自己的 frame + 所有祖先 frame + base frame；写默认落本 frame；改上层需要运行时在审批通过后签发 frameRef + 显式 skill_edit，没有引用连写接口都拿不到；修改产生新版本，运行中的 agent 钉住加载时版本、不热替换；

把 skill 提升到上层 = 对上层 frame 的一次修改，走同一审批；日志记 frameId/version/hash。与 memory 对称：memory 与 skill 都只能通过 report/promotion 向上流动，区别是 skill 是可执行知识，需版本化 + 审批。

### 待定

帧粒度（每节点一帧 / 同父兄弟共享一帧 / 每分支共享）、审批人（目标 frame owner vs 用户）、同名 skill 的 shadowing 规则。

<!-- 20261124-014 -->

## Skill 池最终形态（2026-11-24，用户口述，承 20…

Skill 池最终形态（2026-11-24，用户口述，承 20261124-013）：每个节点有私有池与派生池。私有池只有自己读写；派生池可由母节点和子节点读取；子代理创建的 skill 只能保存在子代理内部（私有池），复制到公共位置需要其母节点操作；类比类的 public/private。

我形式化为 one-hop 可见性：节点可读自己的私有 + 自己的派生 + 母节点的派生 + 子节点的派生；可写自己的私有 + 自己的派生；不能写母节点/子节点的派生。每个派生池的写者是它的拥有者（该层的母节点）；兄弟共享只能通过母节点的派生池：子 report → 母节点复制进自己的派生池 → 所有兄弟可读。

提升一级一级走，母节点复制进自己的派生池即该层审批，再往上由祖母/用户批。

### 待确认

可见性是一跳还是整条祖先链（与上一轮栈模型不同）；节点是否只能写私有、派生池是否只能由母节点写。

<!-- 20261124-015 -->

## Skill ACL 修订（2026-11-24，用户口述，取代…

Skill ACL 修订（2026-11-24，用户口述，取代 20261124-014 的读写规则）：Public 池可以被自己、同级（兄弟）、父级写，但需要相对索引编码（以访问那一特定的 Agent）；Private 的优先级高于 Public。

### 我形式化为

默认 lookup = N.Private > N.Public > parent.Public > ... > base（私有最高，深的公有覆盖浅的）；兄弟/孩子的 Public 不进默认 lookup，必须显式相对寻址。写者 = 自己的 Public、兄弟的 Public、孩子的 Public；

不能写父级及以上的 Public、孙子的 Public、别人的 Private。相对索引建议用稳定 id 而不是数字位次（self / sibling:<id> / child:<id> / parent，后接 public|private/<name>），解析后做关系授权并记绝对 nodeId。

### 新问题

一个 Public 池有多个写者，需要 CAS(expectedVersion) 防静默覆盖；私有 > 公有的遮蔽要报 shadowedBy；兄弟/父写 N.Public 会通过栈影响 N 的整棵子树，影响面比看起来大。

### 待定

兄弟/父写 Public 是直接生效还是提案制。

<!-- 20261124-016 -->

## Skill 读写 API（2026-11-24，用户口述）

写 = 必选 operation + content，可选 location；location 缺省 = Private；location = {direction: up|sibling|down, id?}，up 不需要 id，sibling/down 需要 id；「方向可以是任意可写的方向」。

读 = 按名字索引，skip_level >= 0；skip_level=1 即跳过当前 Private（第一层 Private，其余为向上 Public）。

### 我补的待确认点

①Public(N) 写者因此扩成 N、parent、siblings、children（家庭板），但 write 没有 self 方向，写自己的 Public 没有路径；②up 写父 Public 是直接生效还是提案；③operation 是 skill 名还是动作类型（create/update/delete）；

④读栈是否含 N.Public，skip_level=1 落在 N.Public 还是 parent.Public；⑤skip_level 可用于查看「子节点会看到的版本」（因为子节点不读 N 的 Private）。

<!-- 20261124-017 -->

## up 写改为两阶段审批（2026-11-24，用户口述）

写父 Public 的操作会通知父级，需要父级节点确定后才能写入。

### 我形式化为

write(up) 返回 {requestId, status:'pending'}；父级收到 notice（content、来源子节点、目标路径、expectedVersion）；父级确认才落盘，拒绝/超时返回 rejected/expired；子节点可以 await，也可以继续干别的等事件。

这意味着审批人是目标池的 owner（父级 agent），不是人。

### 待确认

①只 gate up，还是 gate 所有「写不属于自己的 Public」（sibling/down 也跨 owner，而私有>公有只保护 owner 自己不保护子树）；②root/base 级变更是否要人批；③pending 过期与 CAS 冲突处理。

<!-- 20261124-018 -->

## 统一门禁（2026-11-24，用户原话「都加门禁吧，这样代码好…

统一门禁（2026-11-24，用户原话「都加门禁吧，这样代码好写一些」，承 20261124-017）：写自己拥有的池直接生效；写别人的池一律两阶段，owner 确认后才落盘。

### 矩阵

self → 自己的 Private/Public 直接；up → parent.Public 由 parent 确认；sibling → sibling.Public 由该 sibling 确认；down → child.Public 由该 child 确认；root/base 的 Public 由用户确认。

### 后果

父节点不能再单方面给孩子写 skill，down 也要孩子批，父只能提案；给 10 个孩子注入同一 skill 就是 10 个 pending（后续可加批量提案，语义仍一个个批）；Public 池从「家庭板」变成「owner 已接受的提案板」，与「私有 > 公有」自洽。

我拟的 API 默认（待用户点头）：location.direction = self|up|sibling|down，省略 = Private，self 写自己的 Public；operation = skill 名，write 是 upsert + expectedVersion；

读栈 = [N.Private, N.Public, parent.Public, grandparent.Public, ...]，skip_level=k 从第 k 层开始；owner 已归档/取消则 pending rejected，pending 过期也 rejected。

<!-- 20261124-019 -->

## 自写 Public = 免费广播路径（2026-11-24，用户指出

自己写自己的 Public 会导致子节点直接继承，这是不需要审批的高效途径）。由此形成三条分享路径：①self → own Private：免费，仅自己；②self → own Public：免费，整棵子树下次 load 继承（祖先/兄弟可读，但主要效果是向下广播）；

③up/sibling/down 写别人的 Public：一律 owner 确认，属于定向写入。模型可概括为「默认继承 + 子树主权」：祖先的 Public 是默认值，每个节点可以用自己的 Public 覆盖自己子树；更深的 Public 覆盖更浅的；

父节点不能强制改子节点的子树（down 需子节点确认），但父节点可以写自己的 Public 做整棵子树的默认广播（子节点可用自己的 Public 遮蔽）。

### 风险

节点可在无审批下改自己子树的行为；建议父节点订阅子节点 Public 变更做审计（只通知、不门禁）。

<!-- 20261124-020 -->

## v1 收口（2026-11-24，用户原话「这东西是个主动加载的…

v1 收口（2026-11-24，用户原话「这东西是个主动加载的东西」「第一版写成这样的复杂度其实已经可以了」）：①Skill 是主动加载：不进 prompt，agent 需要时通过 load/read(name, skip_level) 取内容，运行时返回内容 + 来源层 + 版本；

需要一个最小目录（名字 + 一句话描述）否则无法发现，算 load 工具的一部分。②用户认为当前设计复杂度已到 v1 上限，不再加机制。v1 范围：Android App（Cordis + Node + WebView、前台服务、打开即根会话）；统一 Agent 基类；异步 mailbox + notice；

预算制派生 + 深度可调 + maxChildren；不可变 preset + 运行时上下文 + 消息；每节点私有 memory SQLite + report；Private/Public skill 池 + 主动加载 + self→own Public 免费广播子树 + 跨 owner 两阶段审批 + CAS；

UI 对话 + notice + 可展开指挥台；手机能力相机/相册、通知、SAF 文件、位置、shell。不在 v1：常驻专家提升、跨节点记忆搜索、批量 skill 提案、日历/通讯录/语音/分享入口、iOS、自修改 preset 的完整 UI。

### 仍缺

首个验收场景、记忆上浮/压缩/根检索三条、具体 schema 与打包。

<!-- 20261124-021 -->

## 验收场景 + 记忆模型（2026-11-24）

①首个验收 = 用少量提示词制作出一个项目；具体化为一句提示词「做一个手机上的待办清单网页，能增删改，数据存 localStorage」，成功标准：工作区有 index.html/style.css/app.js；App 内预览可增删改且刷新不丢；公共记忆有 brief/数据契约/关键决策；各节点私有记忆互不可读；

杀掉 App 重开项目和记忆都在；除首句外不补充需求（审批可点）；整个任务有 token/时间/节点预算上限，超了算失败。②记忆分两层：公共记忆 = 全局公告板 DB（事实、决策、项目 brief、规则；所有 agent 可读；任意 agent 追加 entries 带 author，规则只 root/用户写；

长期跨项目）；私有记忆 = 每节点工作记忆 SQLite（任务状态、草稿、中间发现；只有自己可读；随节点归档，promoted 保留；唯一出口是 report）。这取代之前「只有每节点私有记忆 + report」的单一层设计。

③两个对照：memory 是全局/私有，skill 是子树作用域（事实/规则全体共享，能力按子树隔离）；私有记忆的唯一出口是 report，父节点可把 report 条目追加到公告板并带 sourceNodeId。④待确认默认：公告板任意 agent append-only、修改/归档/规则只 root/用户；

规则注入紧凑摘要 + load_rule，硬规则由 capability 层强制；项目预览用 App 内 WebView + 本地静态服务。

<!-- 20261124-022 -->

## 访问分层（2026-11-24，用户口述

Skill 存储是有规律的、不提供直接访问；全局记忆用填参式；私有记忆用直接编写 SQL）。

我形式化为按爆炸半径分层：①Skill = 结构化 API（load(name, skip_level) / write({operation, content, location})），无路径 / 无 SQL / 无文件系统入口；存储可以是 DB 或版本化目录，但模型永远看不到；

②公共记忆 = 填参式 API（memory_write/search/get，schema 固定 entries/tags/rules，运行时拼 SQL，禁止 ATTACH / raw SQL），rules 只 root/用户走 admin；

③私有记忆 = 每节点 SQLite + private_sql({sql})，允许 DDL+DML+SELECT，必须锁死：只打开本节点 DB 文件、拒绝 ATTACH / VACUUM INTO / PRAGMA writable_schema、不能通过路径访问公共 DB 或其它文件、行数/字节/超时上限、读写连接分开。

### 原则

共享的可执行知识 → 结构化 API；共享的数据 → 填参；私有数据 → raw SQL。

### 待确认

私有 SQL 是否允许 DDL（我按允许收）。

<!-- 20261124-023 -->

## 私有 SQL 与工作区（2026-11-24，用户口述）

①私有记忆允许 DDL，每个 agent 可操作自己的 SQLite 文件；用约定引导而非强制：节点创建时预建 meta(key,value) 与 entries(id,kind,content,tags,created_at,updated_at)；

kind ∈ note/task/finding/decision/question/artifact-ref；自定义表可建但要在 meta 注册 table:<name>，表名避开 meta/entries/sqlite_*；大对象不进 DB，放 workspace 并引用路径；

meta 写 schema_version。约定作为稳定的运行时上下文块注入，不靠 prompt 热改。②默认工作区 = ~/.dsh/workspace/main；~ 在 Android 上解析为 App 私有 home（运行时显式设 HOME/DSH_HOME，DSH_HOME=~/.dsh）；

### 布局

workspace/main（默认项目）、workspace/<name>（其它项目）、agents/<id>/（session log、memory.db）、tasks/<id>/（tree.db、归档）、public/memory.db（公告板）、skills/（结构化存储）、presets/。

文件/shell 工具沙箱以 workspace 根为界。

### 待定

workspace 放 App 私有还是用户可见目录（我倾向 App 私有 + SAF 导出）。

<!-- 20261124-024 -->

## 先私有后公开（2026-11-24，用户口述

私有数据放 ~/.dsh/sub_agents/<agent_id>，工作区也是自己私有的；主要设计思路是先私有后公开；侧边栏内部文件管理器 + 导出到手机其它目录）。

我形式化为系统级原则：Skill（Private 池 → Public 池，owner 审批）、Memory（私有工作记忆 DB → 全局公告板，report/append）、Files（私有 workspace → 公开项目 workspace，publish + owner 审批）。

### 布局

~/.dsh/sub_agents/<agent_id>/{workspace,memory.db,session,skills}（子节点私有）；~/.dsh/workspace/main（公开项目，验收产物）；~/.dsh/public/memory.db（公告板）；

~/.dsh/tasks/<id>/（tree.db、归档）；~/.dsh/presets/。上一轮 workspace/main 明确为公开项目区，每个 agent 默认工作区改为自己的私有 workspace。

文件发布建议与 skill 写同一套门禁：子节点 publish({paths,message}) 从私有 workspace 到公开 workspace，root 审批；哈希检测冲突；root 作为 owner 可直接写公开 workspace；公开 workspace 是预览与导出对象。

内部文件管理器为人类专用（可浏览所有私有目录与公开区），导出走 SAF；agent 不能调用它绕过沙箱。

### 待定

①根节点私有数据放 ~/.dsh/root/ 还是也放 sub_agents/root；②根的工作区是私有再 publish，还是直接就是 workspace/main（公开）；③公开 workspace 是单一 root-owned，还是每个父节点都有自己的公开 workspace（层级合并）。

<!-- 20261124-025 -->

## 导出范围（2026-11-24，用户

从 workspace 下选，最高只能导出整个工作区）：内部文件管理器/导出的根是 Workspaces，不是 ~/.dsh；可选公开项目 workspace/main 与各 agent 的 sub_agents/<id>/workspace；最高导出单位 = 一个完整 workspace；

不能导出 memory.db / session / skills，也不能一次导出多个 workspace；整机备份是另一个 admin 功能，不混进这个 UI。

### 导出流程

选 workspace → 选子路径或整区 → SAF ACTION_OPEN_DOCUMENT_TREE 选目标 → 在目标下新建 <workspace>-<timestamp>/ → 递归复制 → 进度/取消 → 返回落点；默认新建目录避免覆盖冲突，v1 不做覆盖确认。

### 边界

agent 私有记忆与日志永远不出 App；用户能带走的是项目产物与 agent 工作文件。

### 仍开

根节点私有 vs 直接用公开区；公开 workspace 单一 root-owned vs 层级。

<!-- 20261124-026 -->

## 文件编辑器的两级视图（2026-11-24，用户

workspace 目录下时，文件编辑器显示的是 Workspace 列表，而不是文件浏览页面）：Level 0 = Workspace 列表，workspace 是一级对象（名称、类型 public/agent-private、owner、大小、最后修改、状态；

### 行操作

打开、导出整个 workspace；列表来自 workspace 注册表而不是扫目录，否则临时目录也会变成 workspace）；Level 1 = 选中 workspace 内的文件树 + 编辑器（面包屑 Workspaces/<name>/...；可查看/编辑；导出当前目录，最高 workspace 根；

返回列表用面包屑，不通过 .. 翻到原始 workspace/ 目录）。因此导出只能从某个 workspace 内部发起，最高整个 workspace，不存在在 workspace 根多选多个目录的入口。

### 待定

列表是否显示 agent 私有 workspace（我倾向显示但默认折叠，标「Agent 私有/调试」；公开项目 workspace/main 默认展开）。

<!-- 20261124-027 -->

## workspace=null 即无文件工具（2026-11-24，用户

「就是没有工具了」）：不是调用被拒，而是工具目录在 spawn 时按 capability 构建；没有 workspace 就根本没有 file/shell 工具，模型看不到。

仍保留 memory、skill、消息（assign/steer/ask/report/cancel）、notice、spawn（受深度/预算限制）。工具集和 prompt 一样是实例级的，spawn 后不变，不存在「后来给了 workspace 就多出工具」。

A/B 用户未点，我按 A 收：root 有私有 workspace，publish 到公开 workspace/main；公开 workspace 单一 root-owned，层级合并留 v2。v1 设计基本闭合，剩余为 schema、包结构、Node 打包、Android 前台服务、第一版 UI。

<!-- 20261124-028 -->

## 实现进展（2026-11-24，agent-tree 阶段 1，…

实现进展（2026-11-24，agent-tree 阶段 1，提交 a3c88ff）：目录 D:\Projects\Deepseek_Harness_Workspace\agent-tree（独立 git 仓库），纯 Node 24 ESM、无外部依赖、node:sqlite（本机 24.22.3 无需 --experimental-sqlite）。

### 文件

docs/V1.md、src/{tree,agent,presets,private-memory,public-memory,skill-store,workspace,session-log,errors,ids}.js、test/*.test.js、demo.js。

### 已实现

统一 Agent 基类/树/邮箱；assign/steer/ask/report/cancel + 内部 reply；notice；

spawn 的 preset/budget/remainingDepth/maxChildren/capabilities/workspace，workspace=null 无文件工具，深度 0 无 spawn，setDepth 运行时可调；preset 不可变；

私有 SQLite（meta/entries、DDL、拒绝 ATTACH/VACUUM INTO/PRAGMA writable_schema、单语句）；公共 SQLite（entries/rules、填参式、append-only+author、rules 仅 root）；

Skill private/public、读栈+skip_level、self/up/sibling/down、跨 owner pending/approve/reject/expire+expectedVersion、history；workspace 继承 + publish 门禁；compaction 摘要。

### 测试

node --test --test-isolation=none test/*.test.js → 50 项全过；npm test 会把 test/helpers.js 也当一个无用例文件计 51。

沙箱禁止 node:test 的 per-file 子进程隔离（spawn EPERM），npm script 已加 --test-isolation=none。demo.js 跑 3 层树成功，产出 public index.html/app.js/PLAN.md。

偏差/未决：显式读取子节点 public 未做（仅向上栈 + 写门禁）；notice 到 agent 只记录不进邮箱，审批走 approveSkill/approvePublish；日志轮换最小（无 zip）；无 shell；

budget 为树级 node cap + per-agent units，无 per-spawn node 切片。

### 未做

Web/Android/Cordis/真实模型/文件管理器/验收项目。
