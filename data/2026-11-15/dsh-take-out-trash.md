<!-- 20261115-008 -->

## `trash` 工具加必填 `description`（R-005 合规），并把模型可见文案全部改成英文（R-006）

（`D:\Projects\Deepseek_Harness_Workspace\dsh_plugins\take-out-trash`，commit `6b94379`，重启加载后已实测）。

### 新参数

`description: string` 必填（与 `paths` 同级）。

JSON Schema `required: ['description','paths']` + 代码 `normalizePurpose()` 双校验：非字符串 / trim 后为空 / 含控制字符或换行 / 超 500 字符都抛 `invalid `description`: …`。

用途进审批卡（`displayReason` 中英双语：英文 `Agent's stated purpose:`，中文「Agent 说的用途」），并作为结果第一行 `Purpose: …`；输出 schema 增加 `purpose` 字段并在结果里回显。

### 顺带改动

工具描述、参数说明、结果渲染、错误信息、`trash.ps1` 的 marker 文本一律改成英文（R-006）；审批卡仍保留中英两版，README 与 locale 保持中文。

**实测（2026-11-15，重启后）**：带 description 删除 2 个测试文件 → 结果第一行 `Purpose: …`、正文英文、两项 `trashed`；

缺 description → `invalid `description`: expected the reason this call is needed`；空白 description → `purpose must not be empty`；

`Tool.listTools` 显示 `trash` 的 `required` 为 `["description","paths"]`。

### 注意

harness 执行层不会因缺必填字段而拒绝调用——缺字段的调用会进到插件里，是代码校验收的尾，所以 schema 与代码两道都要留着。测试 14 项全过（新增 normalizePurpose 校验、注册 schema/execute、Purpose 渲染三组）；测试条目已从回收站清掉，临时目录已删。
