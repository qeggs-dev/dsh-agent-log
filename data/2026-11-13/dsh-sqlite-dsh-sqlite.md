<!-- 20261113-009 -->

## dsh-sqlite 的六个工具都要求 descrip…

dsh-sqlite 的六个工具都**要求** `description`（schema 里 required，运行时缺失或空白直接报错）：一行说明「哪个文件 + 为什么」（如 `MEMORY.db - 核对调用行`），≤500 字符，非字符串报错；**没有别名参数**，旧的 `reason` 已移除且会被忽略。

### 关键事实

会话 UI 的调用行由客户端 `dsh-client-ui-tool` 的 `toolRowModel` 生成——对未知工具优先读 `description` 参数，否则退回第一个字符串参数，**不读 `presentCall`**（time_perf 的 presentCall 标题同样不显示）；

用 `description` 后调用行显示为 `工具调用 · sqlite_schema · MEMORY.db - 核对调用行显示文件与说明`。结果末尾仍回显一行 `reason: …`。测试 46 项全绿。
