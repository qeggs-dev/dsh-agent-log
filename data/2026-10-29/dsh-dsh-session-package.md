<!-- 20261029-002 -->

## 插件「会话包」v2（重做版）

（`〈工作区〉/dsh-session-package`，包 `@local/dsh-session-package` v1.0.0，desktop profile bundle，entry `include:session-package`，`application: applied`）：**只做单会话导出 + 拖放导入**。

导出＝会话列表「…」菜单 **order 500（放在最下面，避开有快捷键的项）** 的「导出会话包 (.dhs)」，下载 `dsh-session-<id>.dhs`（默认带子会话与附件）；

导入＝把 `.dhs`/`.dhb` 拖到侧边栏（`shell.overlay` 里的 fixed 拖放层，用 `elementFromPoint(8, h-12)` 向上找高窄祖先测侧栏宽度，背景用宿主 `--dsw-alias-bg-mask-drop`（亮色白纱 / 暗色深纱）而不是自调品牌色；

**没有任何导入按钮**），完成后右下角 toast，可「打开」首个导入会话；会话菜单导出项 hover 必须用宿主 `--dsw-alias-interactive-bg-hover`（亮色加深 / 暗色提亮），用 `bg-layer-2` 会在亮色下变成白色（高亮“反了”）。

### 格式

ZIP：`index.json`（format=`dhs`（读兼容旧 `dshs`）/ formatVersion=1 / kind=`session`|`bulk` / root 仅单会话 / sessions / attachments / counts）、`empty_dirs`（无后缀 JSONL，一行 `{"path":"..."}`，空目录的权威来源；

导入解包到临时目录时逐个重建）、`session/<id>/session.jsonl`（header + 每行一个 v4 事件，seq 从 0 连续）、`attachments/media|files/...`；`.dhb` 只用于导入多会话（kind=bulk），导出永远 `.dhs`。

### 无第三方依赖、不联网

ZIP 读写用 `node:zlib` 自写（`lib/zip.js`：CRC32 校验、UTF-8、DEFLATE/stored、zip-slip、大小/条目上限、ZIP64/加密明确拒绝），所以此前用户提的「从 CDN 下库再缓存」不需要。

导入走 `create(header,{inheritedEventCount})`+`append`+`flush`；附件经 `saveImage`/`saveFile` 恢复，并按需重写事件里的 `attachmentId`；

根会话用 `workspace.attachSession()` 挂回 cwd 对应工作区；冲突默认 `skip`，工具可 `copy`。

### 一套 Host 实现

工具 `session_package_export`（仅单会话）/ `session_package_import`（.dhs/.dhb），路由 `GET /api/session-package.export`、`POST /api/session-package.import`；

**没有** inspect / 批量导出 / 导入按钮 / 侧栏 hub / header 按钮（前一版全部删除重做）。真实桌面 E2E：导出 20 事件会话 9706 B、empty_dirs 3；skip 导入 0 导入/1 跳过；copy 真实生成新会话并挂工作区（测试副本已删）。

### 测试

`tests/zip.test.mjs` / `format.test.mjs` / `host.test.mjs` 全 PASS（ZIP 往返/CRC/穿越/损坏、JSONL/empty_dirs/index、单会话/父子/附件导出、skip/copy/多会话 .dhb/附件 id 重映射）。

### 未验证

拖放高亮与真实鼠标交互（无浏览器控制）。
