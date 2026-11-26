<!-- 20261025-003 -->

## DataServer 追加存在检查与分片存储

`GET /operations/exists/{path}` 始终返回 200 与 `{"exists": bool, "type": "file"|"directory"|null}`（缺失路径不报错）；文件内容改为两级分片 `files/<xx>/<yy>/<uuid>.bin`（UUID hex 前 4 位），代码中不保留迁移逻辑。旧数据已手工迁移：`running\workspace` 唯一一条 `skill/msg_output.md` 从 `files/<uuid>.bin` 移到 `files/70/10/<hex>.bin`（760 B，哈希一致），`develop` 无数据；两边 `configs/config.json` 的 `base_path` 已从 `./static` 改为 `./workspace`，`.gitignore` 的 `static/` 同步改为 `workspace/`；`running\data_server` 已用 develop 的 `data_server` 整体覆盖（保留 `configs/`、`workspace/`、`logs/`、`.venv`），服务当前未启动；新增 `GET /operations/glob/{path}?pattern=...&recursive=true|false`（recursive 默认 false，true 等价于原来的 rglob）、`GET /operations/list/{path}?recursive=true|false`（recursive 默认 false，true 等价于原来的 rlist；返回值统一为完整虚拟路径）、`/operations/rematch/{path}?pattern=...`；`glob`/`list` 的索引遍历与递归删除子树收集改为 `asyncio.to_thread`；测试 182 个全通过。Backend `DataClient` 同步新增 `exists`、`glob(..., recursive=False)`、`list_dir(..., recursive=False)`、`rematch`。

<!-- 20261025-004 -->

## Backend `core/tool_caller/tools/…

Backend `core/tool_caller/tools/workspace_tools` 已补齐为 11 个工具：`workspace_read` / `write` / `delete` / `exists` / `glob` / `rematch` / `list` / `info` / `mkdir` / `move` / `copy`（glob 与 rglob 已合并为 `workspace_glob` 的 `recursive` 参数；list 与 rlist 已合并为 `workspace_list` 的 `recursive` 参数）；`workspace_delete` 支持 `recursive`。文档在 `docs/tool_calls/built-in/workspace/`，索引编号 22–32；文档里保留了 Data Server 前置配置说明，但 `tool_calls.registed` / `allowed_by_default` 未改动，需要部署侧自行加入这 11 个名字。
