<!-- 20261119-001 -->

## 建立插件 dsh_plugins/official-proto…

建立插件 `dsh_plugins/official-protocol-switch`（@local/official-protocol-switch，bundle 行 id `official-protocol-switch`，独立 git 仓库，初始提交 bd11d5a；

默认 config `enabled: false`）。

### 目标

保留 DSH 的官方提供方身份 `deepseek-official`，但把它的线上协议换成另一条路由的协议。

### 机制

监听 `llm/stream` 瀑布（`dsh-llm/src/index.ts:1193` 包裹 adapterStream，`prepareCall` 在 `next()` 内 :1095）；

对 `options.provider === provider` 的调用不调 `next()`，而是 `ctx.llm.stream({ ...options, provider: route, model })` 重新进入运行时，由目标路由（例如 `@deepseek-ai/dsh-llm-pi-ai` 的 openai-completions 路由）做协议翻译。

因为 provider id 不变，按 id 识别的行为全部保留：免费 Messages web 搜索（`dsh-web` 的 DEEPSEEK_MODEL_ROUTES）、DeepSeek Search/Fetch 的 key 选择、付费翻译、SDK 默认提供方、模型/设置页排序与 DeepSeek 卡片。

代价（官方适配器不运行）：会话日志上报字段与插件清单字段（经 `deepseekLlmApiExtensions` 注册、由官方适配器消费）不发送；不跟随官方 `/models` 列表；Messages 特有的 Files API/内联图片预算改由目标适配器处理。

外层的 `prepareCall` 仍由官方适配器执行，所以目标模型 id 必须能在 DeepSeek 卡片的模型目录里解析（跟随官方列表时 `admit` 会拒绝列表外模型，切手动目录即可）。

### 决策

用户 2026-11-19 选择「先出插件骨架、协议自填」，开关用插件配置的全局开关（不做会话级/斜杠命令）。骨架含 index.js、cordis.patch.yml、locale、icon（复用 dsh-opener 鲸标）、README、tests/smoke.mjs（假 ctx 驱动 apply，全部用例通过；

bundle patch 用安装版 yaml 库解析通过）。尚未 install_bundle，未装入 profile。 2026-11-19 已 `install_bundle` 到 desktop profile（pnpm link，application: applied，warnings 空）；

Config 目录条目 id 为 `include:official-protocol-switch`，status `absent` —— 包没有导出 Config schema，所以 GUI Plugins 里只有行与启停、没有配置表单，参数改 profile patch。

linked 插件目录无法解析 `@deepseek-ai/schemastery`（已实测 ERR_MODULE_NOT_FOUND），要加表单需在该目录 pnpm install 依赖或写 client 半；改 JS 需重启才加载新模块代。

 2026-11-19 追加（v1.1.0，commit 47621a3）：GUI 入口改为「设置 → 通用」一行开关。

Host 端用 `createRequire(join($DSH_INSTALL_DIR, 'package.json'))('@deepseek-ai/schemastery')` 借宿主自带 schema 建 `Config`（enabled/route/modelMap = volatile，provider/onMissingRoute 结构性），零依赖且跨副本安全（cosmokit volatile 用 Symbol.for）；

Client 端（client.js，dsh.client platform web）注册 `settings.general.item`，经 `ctx.configForms.get('official-protocol-switch')` 读写、`whileServed` 门控，开关写 enabled 后 Host 监听器每请求重读引用即生效。

未重启验证。
