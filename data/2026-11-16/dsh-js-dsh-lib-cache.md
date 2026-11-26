<!-- 20261116-009 -->

## dsh-lib-cache 加 npm 源（0.2.0，提交 2436133）

（`dsh_plugins/dsh-lib-cache`）：除原有 URL+id 外，现在接受 `fetch('npm:diff@^9', id)` / `fetch({npm, id, file})`，语义仍是「进一个源、出一个可直接 import 的单文件」。

### 解析链

`npmRegistry`（默认 registry.npmjs.org 的缩略 packument）按 dist-tag / 精确版本 / range 选出一个版本（自写 `lib/semver.js` 支持 ^ ~ >= 1.x || 与 npm 的 prerelease 规则）→ `npmCdn`（默认 unpkg；

本机 jsDelivr 不可达）取文件；省略 file 时读该版本 package.json，按 unpkg→jsdelivr→browser→module→main→exports["."] 选入口并对候选逐个 HEAD 探测（404 跳过）。

**版本标签 = 解析出的 npm 版本**（`get(id,'9.0.0')` 可直接命中），记录带 `npm:{name,range,file}`；

缓存已满足 range 时**零网络**，`refresh(id)` 按记录的 range 重解析（`^9` 能跟到 9.1.0），版本没变则靠 ETag 304 不新增。

### 真实网络实测

`npm:diff@^9` → 9.0.0，入口 `dist/diff.js`（111,301 B）——diff@9 的 package.json **没有 unpkg 字段**，走的是 main，想要压缩版必须显式 `file:'dist/diff.min.js'`；二次调用零网络、refresh 仍 1 个版本。

### 测试

semver 5/5、npm 7/7、store 7/7（本地假 registry+CDN 的完整 npm 链路：解析、入口探测、升级、304、离线、错误分支）、host 1/1（真 Cordis 上下文里经服务走 npm 源，HTTP 200/304）。

### 边界未变

只取一个文件、不解析依赖树（ssh2 这类多文件 CJS 仍 vendoring），`allowNetwork:false` 时 npm 源只读缓存。

**改的是本地插件源码，运行中的 Host 仍是旧模块，需重启 DSH 才生效**（重启前 `fetch('npm:...')` 报 `library URL must be http(s)`）。

（2026-11-19 更正：npm 源已改为缓存整包、入口固化、包内相对 import 可用，见 id:20261119-002；本条里「只取一个文件 / 入口探测」只适用于 0.2.0。）
