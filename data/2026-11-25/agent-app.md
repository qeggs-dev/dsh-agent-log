<!-- 20261125-002 -->

## 1.1 完成（2026-11-25，agent-tree，提交…

1.1 完成（2026-11-25，agent-tree，提交 e8731b2，基于 a3c88ff）：①子节点 Public 读取/复制：tree.skillReadChild（仅直接子、仅 public）、tree.skillCopy（从直接子 public 复制到自己的 private/public，或另一个直接子 public；

目标非自己时 pending + 审批）；SkillStore.readPool + private 读拒绝；跨 owner private 写直接拒绝。

②publish TOCTOU：approvePublish 先按 manifest 读源字节重算 sha256，任一不一致返回 conflict + sourceChanged，一个文件不复制；复制使用已验证 buffer。

③路径对齐：公共 workspace = home/workspace/main，私有 = home/sub_agents/<ownerId>/workspace（root -> sub_agents/root/workspace）；registry 存 path，list() 返回 path；

demo/tests/README 更新。④审批投递：新增 approval_request 消息类型；skill/publish pending 时除 notice 外投到目标 owner mailbox；owner handler 可直接 approve/reject；

skill/publish 过期仍给 requester 发 report。⑤防御：SkillStore.write 拒绝跨 owner private；

workspace read/write/list/publish 用 lstat + realpathSync.native 防 symlink/junction 逃逸（Windows 的 JS realpath 不解析 junction，必须 native）。

### 测试

node --test --test-isolation=none test/*.test.js → 63 项全过；npm test → 64（含 helpers 文件）。未改 MEMORY.db schema、UI/Android/Cordis/LLM。

<!-- 20261125-003 -->

## 阶段 2a 完成（2026-11-25，agent-tree，提…

阶段 2a 完成（2026-11-25，agent-tree，提交 5974663）：①工具目录 src/tools.js 成为单一来源（22 个工具：name、英文 description、JSON schema、handler、visible）；Agent.tools() 从目录派生；

覆盖 core message/ask/report/notice、memory 4、skill 5（含 skill_read_child/skill_copy）、file 4、spawn、approval 4。

②executeTool 先参数校验（缺参/多参/类型错→InvalidToolArguments）、再可见性、再调 tree API，统一返回 {ok,result|error}，不抛到 loop；

每次调用 emit tool_called（agent/tool/args 摘要/ok/耗时），content 只记长度。

③src/loop.js：AgentLoop({agent,model,maxSteps})，context = system preset + runtime context + mailbox 消息 + tool 结果；ScriptedModel 支持数组/策略函数；

approval_request 在 owner loop 可见并可调 approve_*；maxSteps 停止。④测试：node --test --test-isolation=none test/*.test.js → 71 项全过；npm test → 72（含 helpers 文件）。

未接真实 LLM/Cordis/UI/Android；未改 MEMORY.db schema；docs/V1.md 增工具目录一节，README 增 Tools and loop。

### 已知缺口

ask 的工具化只覆盖调用端，被问方尚无模型可调用的 reply 工具（agent.reply 仍是编程接口），待 2b 决定。

<!-- 20261125-004 -->

## 阶段 2b 完成（2026-11-25，agent-tree，提…

阶段 2b 完成（2026-11-25，agent-tree，提交 4b406b0，基于 5974663）：①Provider：src/provider.js 提供 ModelProvider + DeepSeekProvider，OpenAI 兼容 /chat/completions，tools + tool_choice=auto，解析 tool_calls/content/usage；

key 从 DEEPSEEK_API_KEY 读，DEEPSEEK_BASE_URL / DEEPSEEK_MODEL 可覆盖；key 只存私有字段，HTTP/网络错误会 redact，不写日志/仓库。提供 toChatMessages / toOpenAITools，压缩后可丢弃不完整 tool pair。

mock HTTP server 验证请求/响应映射；live 测试由 DEEPSEEK_API_KEY 门控，未设 key 默认 skip。

②Loop：真实 provider tool_calls → assistant tool_calls + tool_call_id → executeTool → tool 消息 → final；usage 累计到 loop.usage 和 agent.spentTokens；

保留 maxSteps、wall-clock、错误信封和 tool audit；ask 触发且模型未显式 reply 时用 final 自动 reply。③补 2a 缺口：notice 可见性跟 notice capability；message 只允许父→直接子，ask 只允许父↔直接子（越界拒绝）；

新增 reply({messageId,payload})；新增 root-only memory_public_rule_add。④预算/压缩：每 agent tokenBudget（默认 100000，AgentTree({tokenBudget}) 可配）+ spentTokens；

超预算停止并向父 report（root 用 notice）；context 超阈值做确定性摘要写 private memory（kind=summary）并替换旧消息。

⑤测试：node --test --test-isolation=none test/*.test.js → 85 tests / 84 pass / 1 skipped（live，无 key）；npm test → 86 / 85 pass / 1 skipped。

本轮未实际跑 live（DEEPSEEK_API_KEY 未设置）。未接 Cordis/UI/Android；未改 MEMORY.db schema。

<!-- 20261125-005 -->

## 阶段 3b 完成（2026-11-25，agent-tree，提…

阶段 3b 完成（2026-11-25，agent-tree，提交 08ce6e0，基于 25aa0c3）：Cordis 4 集成。依赖 cordis@4.0.0-rc.12 + yaml@2.9.1，从 npm registry 安装（非 vendor，package-lock 固定；README 写明版本/来源）。

新增 src/cordis/assemble.js（cordis.yml + cordis.patch.yml 按 row 深合并、Config 预校验、装配后检查 FiberState.ACTIVE、失败 dispose 整个 ctx）、config.js/configs.js（Standard Schema 校验）、plugins/agent-tree.js（树生命周期 + memory/skill/workspace 服务）、model-provider.js（scripted/deepseek，baseUrl/model/timeout，key 只从 DEEPSEEK_API_KEY）、tool-registry.js、plugin-loader.js。

PluginLoader 从 <home>/plugins/<name>.mjs 加载，两阶段 owner/root 审批（plugin_load 只 pending，approve_plugin/reject_plugin 决定，plugin_unload 卸载），写 plugin_audit 与 loader.audit；

拒绝/mount 失败不留半挂载；unload 后 registry 回基线，assembly dispose 后 registry=0。tree.close 现在拒绝 pending ask 并关闭 SQLite。

新增 bin/dev.js + npm run dev（建树→scripted loop→打印事件/DB 关闭）；cordis.yml + cordis.patch.yml；plain npm test/demo.js 保留。

### 测试

node --test --test-isolation=none test/*.test.js → 92 tests / 91 pass / 1 skipped（live DeepSeek 无 key）；npm test → 93 / 92 pass / 1 skipped；新增 Cordis 测试 6 项。

仍是 plain 的入口：demo.js、plain runtime/provider/tools/loop 测试；Cordis 入口是 npm run dev。未改 MEMORY.db schema；未接 Web UI/Android。

<!-- 20261125-006 -->

## 阶段 3c 完成（2026-11-25，agent-tree，提…

阶段 3c 完成（2026-11-25，agent-tree，提交 dbe7fb5，基于 08ce6e0）：①新增 src/runtime.js AgentRuntime：attach() 给 root 装 AgentLoop 并订阅 agent_spawned 给新子节点装同一 model 的 loop（已有 handler 跳过、不覆盖手装 loop）；

每 loop 用 per-agent tokenBudget + defaults 的 maxSteps/wallClockMs/maxContextChars/keepRecent（数字或函数）；

sendUserMessage 通过 tree.sendUser 以 from='user' 的 assign 投给 root；whenIdle 等 tree.idle + active loops，超时返回 timeout 状态不抛；dispose 只移除自己装的 handler 并清 wait 定时器。

②tree 新增 subscribe/sendUser，close 拒绝 pending ask；

Cordis 新增 agent-runtime 插件（inject agentTree+modelProvider，scripted 按角色脚本/ deepseek 共享 provider），cordis.yml 加行，npm run dev 改用 agent-runtime 服务。

③新增 scripts/acceptance.js（npm run acceptance）：无 DEEPSEEK_API_KEY 打印 skip 退出 0；

有 key 时建树、装 DeepSeekProvider+AgentRuntime、发验收句、whenIdle，打印事件数/各 agent tokens/public workspace 文件/public memory/skills；

参数 --prompt/--home/--token-budget/--max-nodes/--timeout；结果目录 .data/acceptance-<ts>，不打印 key；本轮未跑真实 API（无 key）。

④plain 无 plugin loader 时 plugin_load/plugin_unload/approve_plugin 不可见且 executeTool 返回 ToolNotVisible，已加测试确认。

### 测试

node --test --test-isolation=none test/*.test.js → 96 tests / 95 pass / 1 skipped（live DeepSeek 无 key）；npm test → 97 / 96 pass / 1 skipped。

新增 runtime 测试 3 项、Cordis 测试增至 7 项。docs/V1 §16/§17、README runtime/acceptance。未改 MEMORY.db schema；未接 Web UI/Android。

<!-- 20261125-007 -->

## 阶段 3d 完成（2026-11-25，agent-tree，提…

阶段 3d 完成（2026-11-25，agent-tree，提交 9f846e9，基于 dbe7fb5）：①新增 src/skills.js DEFAULT_SKILLS，第一条 build-project（brief/contract 写 public memory、spawn planner 预算≤父剩余一半、planner 拆 2–4 并行文件任务并 ask worker、planner file_list/file_read 集成并 report、root publish→approve_publish→file_list area public 确认、私有 workspace 不算交付）；

建树时在 root context 生成前把种子写进 root public 池，已存在不覆盖；root 与后代通过栈可见。

default preset 加稳定指针“When the user asks for a software project, load the build-project skill first, then plan and delegate.”；

contextMessage 增加 skills 目录（name/description/scope）。②file_list 支持 area:'public'（root/public owner）确认公开交付物。

③acceptance.js 增加每个 agent 私有 workspace 文件、public 文件、delivered 与 status：public 无文件则 failed + reason；不自动 approve，模型须按 playbook publish/approve；参数/预算不变；

无 key 仍 skip，未跑真实 API。④测试：node --test --test-isolation=none test/*.test.js → 99 tests / 98 pass / 1 skipped（live DeepSeek 无 key）；

npm test → 100 / 99 pass / 1 skipped；

新增 playbook 测试 3 项（种子/上下文/preset、幂等不覆盖、mock 三层 root→planner→2 workers→ask/report→publish/approve→public 文件与 delivered true）。docs/V1 §18 与 README 已补。

未改 MEMORY.db schema；未接 Web UI/Android。

<!-- 20261125-008 -->

## 阶段 3e 完成（2026-11-25，agent-tree，提…

阶段 3e 完成（2026-11-25，agent-tree，提交 ee2fccf，基于 9f846e9）：①build-project skill 改为 ask 会合：root 写 brief/contract → spawn planner（预算≤父剩余一半）→ ask planner 一次（timeoutMs 240000）拿最终清单 → 同一轮 publish/approve_publish/file_list area public/notice，不处理中间 report；

ask 超时则 file_list 私有 workspace 并 publish 已有文件。

planner 收到 root ask 后 spawn 2–3 worker，ask 每个 worker 一次（timeoutMs 120000）拿 path/size/status，集成自检后回答 root ask，不发中间 report。

worker assign 写文件、被 ask 只回 path/size/status。skill 明确 ask timeout 必须显式给（默认 5s 不够）。

②acceptance defaults.wallClockMs 从 min(timeout,120000) 改为 min(timeout,300000)，避免 240s ask 在 publish 前被 loop wall clock 杀掉。

③减少多余轮次：tree 的 reply 到 pending ask 只 resolve ask promise，不再额外入 mailbox 触发 loop；

AgentLoop 忽略 agent 自发自收的 approval_request / publish_result / skill_request_result，root publish/approve 后不再多跑模型轮。

④测试：node --test --test-isolation=none test/*.test.js → 101 tests / 100 pass / 1 skipped（live DeepSeek 无 key）；npm test → 102 / 101 pass / 1 skipped；

新增 playbook-ask 测试 2 项（单一 root ask/同轮 publish、ask 超时 fallback publish 已有文件），原 3d playbook 测试保持绿。docs/V1 与 README 已更新 ask 会合说明；未改 MEMORY.db schema；

未接 Web UI/Android；未跑真实 API。

<!-- 20261125-009 -->

## 阶段 3a 完成（2026-11-25，agent-tree，提…

阶段 3a 完成（2026-11-25，agent-tree，提交 37b947d，基于 ee2fccf）：headless Web UI。①Server：新增 src/web-server.js（node:http，只绑 127.0.0.1，端口默认 4310，row config 或 WEB_PORT 可覆盖；

静态 web/ 无构建；结构化错误 400/404/405/413；文本读写 1MiB 上限；

静态路径逃逸拒绝）+ Cordis 行 src/cordis/plugins/web-server.js（inject agentTree/agentRuntime/modelProvider/pluginLoader，async apply 等 listen 成功才 ACTIVE，dispose 先关 listener 再放服务）+ bin/web.js + npm run web；

cordis.yml 中 web-server 默认 disabled:true，cordis.web.yml 由 npm run web 打开，dev/test 不绑端口；

默认 provider 仍是 deepseek（key 只从 DEEPSEEK_API_KEY 读），WEB_PROVIDER=scripted 无 key 演示（brief/spawn/notice/final 脚本）。

②API：GET /api/state?since=<seq>（agents 含 id/parent/preset/status/tokens/depth/workspace、events since、notices 带 requestStatus+actionable、publicWorkspace files、workspaces、root skills、public memory entries+rules）、POST /api/message、POST /api/approve|reject（kind = skill/publish/plugin，作为 request owner 决策）、GET /api/agents/:id（preset/workspace/私有 memory entries/skills/session log tail/tools/notices）、GET /api/workspaces/:id/files|file|download。

③事件：AgentLoop 新增 user_message/assistant_message（均带 agentId，final 时发 assistant_message）；前端每 800ms 轮询 /api/state?since=seq 并按 seq 去重。

④UI：原生 HTML/CSS/JS 无构建、移动优先单列+≥900px 双列、暗亮跟随系统；主区连续对话（user/assistant/tool 卡/notice 卡带批准拒绝）+ 底部 composer（Enter 发送、Shift+Enter 换行）；

右栏/抽屉 4 tabs：Tree（可展开、状态/预设/tokens/workspace，点节点显示只读详情）、Workspaces（列表+文件树+只读查看/下载+..向上）、Memory（公共 entries/rules + 选中节点私有 entries）、Skills（选中节点可见 skills）。

⑤测试：新增 test/web.test.js 9 项（state、message 触发 user/tool/assistant 事件、message 400、approve+reject publish、pending skill approve、agent detail、workspace files/file/download+路径逃逸、静态 HTML smoke（composer/tree tab/workspaces tab/notice 模板）、Cordis web 行集成+dispose 关监听）；

npm test → 111 tests / 110 pass / 1 skipped（live DeepSeek 无 key），原 102 项保持绿；未跑真实 API；未改 MEMORY.db schema；未接 Android/SAF/认证，未做节点 steer/cancel。

⑥文档：README 补 npm run web/端口/WEB_PROVIDER/API 表/布局/已知限制；docs/V1 补 §19 Web UI 并更新 §2/§10。
