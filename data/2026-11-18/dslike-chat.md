<!-- 20261118-001 -->

## DSLike Chat 聊天页白屏根因（2026-11-18）

手机端已安装样式包 aurora 的 assets/light/chat.gif 是坏图——IndexedDB 里 16,714 字节、640x400，但像素全黑且 Chromium 绘制为透明（canvas drawImage 得到 [0,0,0,0]），CSS background 因此不显示；当前示例包同资源为 13,381 字节正常渐变（像素 204,204,255 等），写回手机后聊天页背景恢复（截图采样 rgb(214,252,255)）。App 侧 SessionView ::before、CSS 变量、objectURL 生命周期均正常，不是代码 bug；旧导入留下的坏资源导致。附带结论：示例包背景应改用 PNG/WebP，8 位 GIF 有明显抖动。

<!-- 20261118-003 -->

## DSLike Chat 0.3.0（2026-11-18）发布

Preset 页改为预设标签栏 + API设置/模型参数/提示词/记忆/上下文压缩五栏；三协议（anthropic messages / openai chat / responses）经 provider 层统一；用量统计（用量、缓存命中率、生成速率、余额）；sql.js 记忆（sections/entries/entry_tags，memory_write/memory_search 工具 + 最多 3 轮工具循环）；自动上下文压缩（chars/4 估算、阈值 + 保留最近 N 条、摘要 checkpoint 落 Session.compaction）；样式包新增 fit/align/position/render(image-rendering) 与 CSP/白名单安全边界。关键外部约束：DeepSeek Anthropic 兼容端点上，客户端工具与 title/safety_check/服务端工具同时存在时必须处于 thinking 模式，否则 400 "client tools can only be used together with ... in thinking mode"；应用在带记忆工具的 DeepSeek 兼容请求里自动启用 thinking。产物：out/dslike-chat-desktop-0.3.0-win-x64.zip、out/mobile/dslike-chat-debug.apk；web 提交 7de7271，根仓库 949d715。

<!-- 20261118-004 -->

## DSLike Chat 0.3.1（2026-11-18，web…

DSLike Chat 0.3.1（2026-11-18，web 2494d1d / root 3070313）发布：默认预设（id default、内置不可删、空字段走系统默认，wire 与无预设逐字段一致；元信息 名称/描述/作者/版本/版权声明/ID 只读；普通预设必填仍强制）；用量拆分 append-only events + stats/totals（单事务、v1 迁移回填、仅清日志/全部置零、JSON/CSV 导出 RFC4180、移动端提示不支持）；样式包图片 effects（alpha canvas 描边/外发光/内发光/浮雕、CSS drop-shadow、window 归一化裁切、zoom 0–4、tilt 仅 icon.*/cover 且仅资源项内配置）、样式详情页 + cover + 卡片加载/恢复默认、示例包去官方 Logo；内置示例包生成器移到仓库 tools/style-fixture/。新增 docs/architecture.md（项目地图）与 docs/plugins.md（插件系统设计：默认全沙箱 Worker/iframe，首次安装三步确认、按钮左中右随机、之后单次确认）。下一步 cordis-refactor（Phase 1 容器+六服务）→ plugin-runtime。

<!-- 20261118-006 -->

## DSLike Chat 样式包改为按主题提供包图标与整页封面（2…

DSLike Chat 样式包改为按主题提供包图标与整页封面（2026-11-18，示例包 aurora）：manifest 的 `icon` / `cover` 支持 `{ "light": { "file": … }, "dark": { "file": … } }`，旧的 `{ "file": …, "effects": … }` 形式保留为主题无关兜底（代码在 web/src/services/style/zip.ts 的 readManifestImage / resolveManifestImages）；详情页 cover 改为根容器 full-bleed 背景（background-size: cover，不再是小 hero 卡片），代码侧把信息区放在半透明面板上，因此 cover 原来的 outerGlow / tilt effects 已从示例包去掉。示例包 tools/style-fixture/aurora.zip 不再有根 icon.png / cover.png，改为 assets/light|dark/icon.png（1024×1024，浅底深带 / 深底发光两版，40px 下亮版平均亮度约 203、暗版约 32）与 assets/light|dark/cover.png（1440×1920 纵向 3:4、不透明，亮版均值约 232 / 暗版约 34，上/下渐变留可读区）；图标与封面都由 tools/style-fixture/gen.mjs 纯 Node 解析式绘制（无绘图库，PNG Up 过滤），`node tools/style-fixture/gen.mjs` 可重复生成（aurora.zip 约 1.88 MB、20 条；bg-effects / bad-* 四个验证包字节不变，仍是旧 { file } 形式）。桌面壳用 CDP 在亮/暗两套主题下验证：40px 图标选到对应主题版本、cover naturalWidth/Height=1440×1920 且 background-size=cover、标题/描述对封面背景对比度约 16–17:1、滚到底无白边断层。
