<!-- 20261113-004 -->

## 新增桌面插件 **`@local/dsh-plugins-man…

新增桌面插件 **`@local/dsh-plugins-manager`（插件批量管理）**（源目录 `D:\Projects\Deepseek_Harness_Workspace\plugins-manager`，bundle 行 id `plugins-manager`，desktop profile，`install_bundle` 返回 `application: applied`、warnings 空）。

入口是设置 → Plugins 里的新标签页：Client 注册 `settings.plugins.tab`，id `batch`、order 20，label 随 locale 显示「批量管理 / Batch」；

Host 提供 `/plugins-manager/state|export|delete|enable|import|import-path` 六个同源接口。

### 导出

只列 `availability === 'profile' && installed === true` 的包；

单选取包目录内容为 ZIP 根（文件名 `<去@包名>-<版本>.zip`），多选生成 `plugins/<slug>/…` + `manifest.json` + `README.md` + `skills/install-dsh-plugins/SKILL.md`。

manifest 的 `profilePatch` 是从 profile `cordis.patch.yml` 里按 rowId/moduleName 文本摘出的配置块（只作提示，不自动重放）。

### 包目录解析顺序

依赖 spec 的 `link:`/`file:` → profile `node_modules/<name>` → profile manifest 解析；跳过 node_modules/.git 等与符号链接。

### 导入

ZIP 上传或本机目录/.zip 路径；

ZIP 存到 `$DSH_HOME/plugin-data/dsh-plugins-manager/imports/<stamp>/source.zip`、解压到同目录 `unpacked/`，再逐个 `ctx.pluginManager.installBundle(absDir,{enabled:true})`。

因此导入后的 profile 依赖是 `link:` 到该持久目录，**不要删除 imports 下的目录**；按目录导入则原地 link。

结构解析先认本插件 export manifest（`dsh-plugins-manager/export@1`），否则递归找 `package.json`（≤5 层）并要求 `dsh.bundle.patch` 文件存在；同批重名只装第一个。

**删除/启停**：删除走 `removeBundle`（卸载 + 从 profile 删依赖，源码目录保留），启停走 `setBundleEnabled`；当前插件自己被拒绝删除/停用。

所有包操作只经 `ctx.pluginManager`，不手写 profile 的 package.json/cordis.patch.yml。

### 搜索

优先 Fuse.js 7.1.0（`https://unpkg.com/fuse.js@7.1.0/dist/fuse.mjs`），经 `libCache.fetch({url,id:'fuse',version:'7.1.0'})` + `libCache.import` 缓存/加载；

libCache 缺失或下载失败时退回内置加权匹配。实测 state 的 search.status=ready、engine=fuse。

**ZIP 编解码**自带（`lib/zip.mjs`，node:zlib）：CRC32、store/deflate、UTF-8 名、目录项、data descriptor；读侧拒绝加密/ZIP64/多盘/路径穿越/绝对路径/盘符，单条与总计 512MB 上限。

已与 PowerShell `Compress-Archive`/`Expand-Archive` 双向实测（含中文路径）。

### 验证

2026-11-13：state 列出 36 个 profile 包；Fuse ready；单包导出 22,663B 可 Expand-Archive；双包导出 56,693B 含 manifest/skill/两个包；按目录导入 fixture → applied → delete 移除；

ZIP 上传 fixture → 解压到 imports → applied → delete 移除；再导入已安装的多包导出得到两个 `already-installed` 且未破坏现有安装。

Client 侧 `Slots.listSubTree settings.plugins.tab` 已见 occupant `batch` active；**界面视觉未验证**（本机无浏览器控制，未打开标签页）。

### 取舍

不注册 Agent 工具——安装/删除是 profile 级破坏性操作，内置 `plugin_manager` 已有审批；本插件把这类动作留给用户在设置页显式完成。只列 profile 包，内置包仍由内置插件页管理。
