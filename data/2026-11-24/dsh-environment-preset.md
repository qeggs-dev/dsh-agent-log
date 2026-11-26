<!-- 20261124-003 -->

## 新增 DSH 插件 @local/dsh-environm…

**新增 DSH 插件 `@local/dsh-environment-preset`（环境预设，目录 dsh_plugins/environment-preset，独立 git 仓库，已装进 desktop profile 并实测）**：把一套可复用环境（插件源码 + AGENTS.md 规则 + 附件 + 安装 skill）打成一个 `.envpreset`，再解到工作区。

### 工具

`package_env`（参数 pluginPaths / agentsMd / attachments / skill / 可选 packageId、outputDir、overwrite）默认写 `<工作区>/.env_preset/package/<package_id>/<package_id>.envpreset`；

`unpack_env`（参数 path、可选 overwrite）解到 `<工作区>/.env_preset/unpack/<package_id>/` 并在结果里返回安装 skill 正文，不自动装插件、不改工作区 AGENTS.md、不写技能目录（用户 2026-11-24 选择「只解压 + 返回安装 skill 内容」「skill 只放 preset 目录」）。

### 包布局

`manifest.json`（producer + AGENTS.md/skill/附件载荷的 sha256 与计数）、`AGENTS.md`、`skill/SKILL.md`、`plugins/<plugin-id>/...`、`attachments/index.json`、`attachments/files/<id>`。

附件建模按用户要求用「目录 JSON + ID 化文件」：index.json 记录每个根的原始绝对路径、kind（file/directory）、entries 里 file / empty-file / empty-dir 三种条目，载荷按 `att-0001` 这类 ID 存；

解包按索引还原到 `attachments/<att-root-0001>/`，空文件与空目录显式重建。

### 边界与回滚

来源路径默认限工作区内（会话 danger-full-access 或配置 allowOutsideWorkspace 才放开），只写工作区内目标，只读会话不能打包；符号链接跳过并进 warnings；插件 id = 目录名 slug，批内重名报错；

`.git`/`node_modules`/`dist`/`__pycache__`/`.venv`/`.cache` 默认排除；目标已存在默认拒绝，`overwrite: true` 时先把旧目录改名 `.replaced-<id>-<时间戳>` 再换入（不删旧副本）；

解包先写 `.staging-*` 再 rename。

### 实现要点

ZIP 用自带 lib/zip.js（node:zlib，无第三方依赖）；遍历与排除在 lib/walk.js；附件在 lib/attachments.js；构建/读取/安装在 lib/package.js；身份常量在 lib/identity.js。测试 16 个用例全绿（`npm test`）。

分发按 R-020 产出 `dist/local-dsh-environment-preset-1.0.0.tgz`（脚本自写 ustar+gzip，不 spawn npm pack，因为受限会话里 spawn 抓管道会失败）与含 SKILL.md 的 `dist/environment-preset-1.0.0.zip`；

`SKILL.md`、`scripts/build-dist.mjs` 入库，`dist/` 已 gitignore。

踩坑（重要）：工具执行完才校验 output schema，`additionalProperties: false` 下结果里多一个未声明字段（manifest.attachments 带了 index）会让整次调用报 invalid output，但文件已经写出去了；

给 package_env 的结果 schema 补 `index` 后必须重启 DSH 才生效（改 link 插件源码不会热替换 Host 代码，测试幂等时被上一次残留包挡住）。
