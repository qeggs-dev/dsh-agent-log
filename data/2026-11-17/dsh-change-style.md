<!-- 20261117-004 -->

## **change-style 插件（2026-11-17，`〈工…

**change-style 插件（2026-11-17，`〈工作区〉/dsh_plugins/change-style`，包 `@local/dsh-change-style` v1.0.0，desktop profile 行 id `change-style`）**：Host-only，只注册工具 `change_style`。

**`description` 必填（R-005）**；**`style` 可选，省略 `style` 即读取当前外观枚举**（`action: "read"`，不写、不审批），传 `style: light|dark|system` 则切换（`action: "switch"`）。

空参数 `{}` 报 description 必填，不当作读取（见 R-029，取代曾短暂写下的 R-028）。

写的是主题插件 `ui-theme` 的 volatile 字段 `preference`（与「设置 → 通用 → 外观」同一偏好）：`ctx.settings.mutate('ui-theme', [{op:'set',path:['preference'],value}], revision)`，profile `cordis.patch.yml` 的 `ui-theme.config.preference` 同步；

客户端 configForms 订阅设置失效后**已打开页面即时切换**（实测 themeSource=dark、body 带 `data-ds-dark-theme`、背景 rgb(21,21,23)，无刷新）。切换前必须经 `ctx.approval` 一次性授权：只认 `allowed-once`；

rejected 时用 `approval.overrideOf(session)` 区分「用户点拒绝」与「本会话策略 never」；cancelled / unavailable / 无审批服务都失败关闭；目标与当前相同则 `changed:false`，不弹审批也不写。

`settings` 与 `approval` 都是可选服务（`inject` 只有 `tools`，用 `ctx.get()`）。写入后重新 `describe()`，返回 Host 读回的偏好而非请求值，不一致就报错；并发撞 `SETTINGS_CONFLICT` 按新 revision 重试一次。

无客户端 UI / 设置页，只在插件列表一行（locale en/zh + 自绘 icon.svg）。测试 `node tests/change-style.test.mjs` 13 项全绿。

### 实机

`change_style({description})` 返回 `Current appearance style: follow system`；`{}` 报 description 必填；带 style 的子代理调用被策略拒绝即证明审批门生效。

### HMR 经验

单纯编辑 link 包文件不会立即重载（hmr root 默认 `[]`）；

触发重载可用 `plugin_manager set_plugin include:change-style enabled:true`（返回 applied 且 changed:false 也会 recompose 并载入新代码），或任意写 `ui-theme` 设置的设置写入（改 profile patch → recompose）。

git 提交：ca8f0d3 初版 / 7bad896 审批门 / 24d58e9 无参读取（随后被 c2e2eef 纠正）/ c2e2eef description 必填 + style 可选 / bfbfa94 报错措辞。

### 未验证

真实审批卡渲染与批准后的切换（需主会话调用）。
