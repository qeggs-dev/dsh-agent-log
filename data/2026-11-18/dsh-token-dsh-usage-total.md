<!-- 20261118-005 -->

## 新增 DSH 客户端插件 Token 总用量（包名 @loca…

新增 DSH 客户端插件 Token 总用量（包名 `@local/dsh-usage-total`，源码 `〈工作区〉/dsh_plugins/dsh-usage-total`，独立 git 仓库，提交 39ed6fc / a7ed982，bundle 行 id `dsh-usage-total`，已 install_bundle 装入 desktop profile 并 live 生效）。

### 需求

`性能与用量` 选详细时，在底部 Token 用量旁显示主会话 + 全部子代理的合计。

### 实现

客户端在 `conversation.composer.dock` 注册 entry id `usage-total`（order 2，紧跟内置 `usage`）；模式偏好读 `ctx.configForms.get('ui-chat')` 的 `performanceUsage`（缺省 detailed；

设置切换后约 1 秒才反映，因为要等 Host 写入与 mirror 回读）；

本会话用量读 `useProjection('tokenUsage')`，子代理用量取 `useSessions(state => state.byId)` 每行的 `projectionValues.tokenUsage`（缺失时退回 `projectionsBySession[id].values.tokenUsage`），成员关系为「行上 parentId 链」与「subagentCatalog 投影」的并集并做 BFS（含嵌套，external 跳过）；

点击读数弹出主会话 / 子代理（个数、运行中）/ 合计三行。样式遵循 R-026：specific-menu + menu-backdrop-filter + elevation-panel + border-l2。

坑：`number.groupSeparator` 只在 chat 命名空间里，common 词表没有，直接 `t('number.groupSeparator')` 会在界面打印字面 key 并把数字撑爆布局，插件必须自带分组符 key。

### 验证

详细下出现、简洁下隐藏（刷新与实时切换都验过）、Escape 与外部点击关闭、亮暗两套配色正常、2 个子代理合计 144,601 与主会话 29,567,329 相加等于合计；另注意 capture_screen 的窗口模式（WM_PRINT）拍不到 portal 面板，须用整屏截屏。
