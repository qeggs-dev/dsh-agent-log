<!-- 20261115-012 -->

## 新插件 diff-edit（工具 `diff_edit`）

2026-11-15 按用户要求新增，功能是**用统一 diff 改一个文本文件**，diff 引擎用 **jsdiff**（npm 包名 `diff`）。

代码在 `dsh_plugins/diff-edit/`（独立 git 仓库，初始提交 `1593ecc`，10 个文件），已 `plugin_manager install_bundle` 装进 desktop profile（`link:` 符号链接），返回 `application: applied`，`diff_edit` 已进工具表并实跑通过。

**jsdiff 走 `dsh-lib-cache`（R-017，不 vendor）**：`ctx.libCache.fetch('https://unpkg.com/diff@9.0.0/dist/diff.min.js','jsdiff',{version:'9.0.0'})` 再 `ctx.libCache.import('jsdiff','9.0.0')`；

缓存里已有 `files/jsdiff/9.0.0/diff.min.js`，37162 B，sha256 `b51a9d2885f2c090dc97b981027395f7e7e6558a46c75ae3747db267913a89ab`（与 npm tarball 的 `dist/diff.min.js` 同字节）。

### 工具参数

`description`（R-005 必填）、`file_path`、`diff`（单文件）、`fuzz` 0–3、`dry_run`。

### 关键实现取舍

① hunk 的 `@@` 行数按正文重算 —— jsdiff 对错行数只回 `Hunk at line N contained invalid line`，模型几乎总写错；② 起始行号写错也能对上（jsdiff 内部按内容搜索最佳落点）；

③ 写入走 `ctx.fs.writeText(text, intent, signal, policy)`，policy 来自 `ctx.sandboxPolicy.resolve({session})`，intent 来自 `ctx.waterfall('fs/write-intent')`（已读过的文件得到 `replaceIfVersion`），读后/写后都 `ctx.emit('fs/observed')` —— 与内置 write/edit 同沙箱围栏、同 stale 守卫；

④ 新建文件只接受**单个纯加行** hunk（`oldStart` 强制归一到 0）；⑤ 多文件 diff 明确拒绝（`diff --git` 两次 / preamble 两个 `+++` / hunk 末尾出现 `---`+`+++` 头块）。

**jsdiff fuzz 的真实边界（实测+测试锁住）**：新增行**紧邻**的上下文必须精确匹配（`applyHunk` 的 `+` 分支要求 `lastContextLineMatched`），fuzz 开到 3 也救不了；被删行必须逐字匹配。

**纯逻辑**在 `lib/diff-apply.js`（不 import jsdiff），`tests/apply.test.mjs` 37 条全过，默认从 lib-cache 缓存读 diff.min.js（也可 `--jsdiff` 指定）。

### 已实测

创建文件、改文件（行数与行号都故意写错）、dry_run 不落盘、上下文不符时报出第一个失败 hunk 且一个字节都不写、工作区外写入被 `FS_SANDBOX_DENIED` 拒绝、CRLF 保持（3 个 CRLF、0 个裸 LF）、fuzz=1 在非紧邻漂移下生效、已满足的 diff 报 unchanged。

**未验证/已知状态**：装完后我改了工具描述文案，运行中的 Host 仍是安装时那代模块，**重启 DSH 才显示新文案**（逻辑未变）；工具卡片的 diff 渲染与插件图标/标题**没在 UI 里亲眼看过**。

### 另注

DSH 自带一个 `apply_patch`（`*** Begin Patch` 语法，在 `@deepseek-ai/dsh-tool-fs` 里，`applyPatch` 默认 false 未启用），与本插件不是一回事。
