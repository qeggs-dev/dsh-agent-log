<!-- 20261027-001 -->

## Backend 主服务器新增 `/workspace` API（…

Backend 主服务器新增 `/workspace` API（`core/api/_apis/_workspace_api`）：1:1 映射 `DataClient` 的公开操作，直接调用 `runtime.data_client` 的方法（`get_file` / `get_text` / `list_dir` / `glob` / `rematch` / `get_info` / `exists` / `write_file` / `delete`），返回客户端原始结果，不做通用反向代理；`_routes/` 下每个端点一个文件，`_client.py` 提供共享 `get_data_client()`；`close` 不暴露；无额外鉴权。API 文档在 `docs/api_table/workspace_api/`（12 个端点页 + index），并已加入 `docs/api_table/index.md` 的 Workspace API 小节。`DataClient._request` 同时改为把 DataServer 的 4xx/5xx 转成保留原状态码的 `HTTPException`。

<!-- 20261027-002 -->

## DataServer 新增 `POST /operations/…

DataServer 新增 `POST /operations/mkdir/{path}`（自动补齐父目录）、`move`（只移动索引节点，文件 ID/payload 不变，同父目录换名即重命名）、`copy`（递归克隆并为每个文件分配新 UUID、复制 payload）；Backend `/workspace` 补齐 12 个端点、tools 补齐到 11 个；Nonebot `clients/workspace_client` 新增 `WorkspaceClient`（12 个方法）并接入 `clients/__init__`、路由常量和 `workspace` 超时。DataServer 测试 193 全通过；文档新增 Backend API/工具页和 DataServer README/KNOWN；Backend `.gitignore` 的 `workspace/` 改为 `/workspace/`，避免忽略 `docs/tool_calls/built-in/workspace/`。
