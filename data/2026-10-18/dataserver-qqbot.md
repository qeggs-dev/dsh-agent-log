<!-- 20261018-001 -->

## DataServer 项目位于 `D

\Projects\QQBot\DataServer\develop`（Python 3.11.9 + FastAPI 0.143.2，poetry `package-mode=false`，venv 在 `.venv`，版本 1.0.0），把目录虚拟化成 HTTP 文件服务；

2026-10-18 为其补齐 stdlib `unittest` 测试套件 `tests/`（**182 个用例全部通过、0 expected failure**，运行 `.venv\Scripts\python.exe -m unittest discover -v`，无需 pytest/httpx，HTTP 层用自写 ASGI 驱动），同日按用户要求修好了接口缺陷：读写统一到 `_file_path()`、根目录可列、错误映射为 404/400/500、`/operations/info` 返回 JSON、空工作区自动建 `index.json`、`configs/` 自动创建、响应补 `Content-Type`、`write()` 目标不存在时自动创建节点并落盘索引、新增 `DELETE /operations/delete/{path}`（文件/空目录/递归删除；

根目录 403、非空目录 409）；`_create_dir_node()` 已按创建/校验语义修好但仍无调用方；剩余非接口问题 D10–D11（配置键大小写静默失效、`create_app()` 工厂不完整）记录在 `tests/KNOWN_ISSUES.md`
