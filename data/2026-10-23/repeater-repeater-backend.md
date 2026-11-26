<!-- 20261023-032 -->

## repeater-backend 新增 `excludeWork…

repeater-backend 新增 `excludeWorkspaces`，默认配置里已把本工作区 `〈工作区〉` 列进去（用户明确：不希望这个工作区用于对话）：被排除的目录**连候选都不是**——不 stat、不读 cfg、不挂 watcher，即使里面放 `enabled = true` 也不起服务；

它与「cfg 开关关着」的区别是后者还能被打开。同时清掉了 `%DSH_HOME%\repeater-backend\sessions.json` 里属于本工作区与已删 `.tmp-live` 的两条 Session 映射（现在 `workspaces` 为空对象）。

### 遗留

实机验证创建的那条真实 Session（答案「收到」，`session-a47e3c4d-a814-4677-9474-21746903feac`）仍挂在 GUI 的 `〈工作区〉` 工作区下，要删得走 GUI——手动删 JSONL 会与 `storages\session_projcache.json` / `workspace.json` 索引不一致。
