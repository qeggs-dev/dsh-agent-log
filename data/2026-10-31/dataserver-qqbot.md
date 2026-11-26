<!-- 20261031-001 -->

## DataServer/Backend/Nonebot 补齐文件系统接口

`is_file` / `is_dir`，`append` / `truncate` / `touch` / `edit`，`hash` / `du` / `tree` / `copy_range`。DataServer 21 个 operation、Backend 22 个 `/workspace` 路由 + 22 个工具、Nonebot `WorkspaceClient` 22 个方法；测试 203 全通过（FM 75 / API 46）；文档补齐到 22 个 API 页、22 个工具页，链接 0 断链；develop 配置已加入全部 22 个 workspace 工具；running 已同步。

<!-- 20261031-002 -->

## Backend `core/tool_caller/tools/…

Backend `core/tool_caller/tools/realspace_tools` 提供 22 个现实路径工具（read/write/append/truncate/touch/edit/delete/exists/is_file/is_dir/glob/rematch/list/info/mkdir/move/copy/get_url/hash/du/tree/copy_range），直接使用 `pathlib` 操作本地文件，不经过 DataServer/DataClient；`_fs.py` 统一做路径解析，白名单读取 `tool_calls.tools_configs.realspace.writelist`，空白名单拒绝所有操作；工具已在 `tools/__init__.py` 注册，但未加入 develop 的 `tool_calls.registed`。
