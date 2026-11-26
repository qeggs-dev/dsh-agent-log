<!-- 20261028-003 -->

## DataServer `GET /operations/read…

DataServer `GET /operations/read/{path}` 支持标准 `Range` 请求头：`206 Partial Content` + `Content-Range`，非法/越界 416，`FileManager.read(start,length)` 只读区间；

Backend `DataClient.get_file_response/get_file/get_text` 支持 Range 与任意请求头，`/workspace/get_file` 透传 `Range`/`If-Range` 并返回 206/`Content-Range`，`workspace_read` 增加 `offset`/`length`；

Nonebot `WorkspaceClient.get_file(start,length,headers)` 同步支持 Range，`Response` 增加 `.headers`。DataServer 测试 197 全通过，running 已同步。
