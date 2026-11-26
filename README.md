# 工作区日志

固定外壳 + 两级索引 + Markdown 正文。页面写一次不再动，每天只多一个数据目录。

```
index.json                        根索引：所有天、最新条目、元信息
data/<date>/index.json            当日索引：板块 → 正文链接 + 关键词
data/<date>/<slug>.md             正文（Markdown，GitHub 上也能直接读）

index.html                        外壳
assets/app.js                     读索引 → 读正文 → 渲染
assets/markdown.js                只渲染生成器会产出的 Markdown 子集
assets/style.css                  样式（跟随系统深浅色）

scripts/build_data.py             生成器：MEMORY.db → 上述数据
scripts/build-preview.py          把整站打成单文件 preview.html

tests/markdown.test.mjs           渲染器测试
.gitignore
.nojekyll
```

## 为什么生成器在仓库里

数据是生成的，**生成器就是格式契约的唯一实现**。它和数据在同一个仓库、同一条历史里：
哪天格式变了，`git log` 能同时看到「改了脚本」和「从哪天起数据长这样」。

每份产物还带版本戳：

- `index.json` 与 `data/<date>/index.json` 里都有 `"generator": "build_data.py 2.1.0"`
- `schemaVersion` 只在**破坏性变更**时加一；加一意味着外壳必须同时改

改脚本时：改 `SCHEMA_VERSION` 还是版本号，取决于是否破坏了已发布的数据——不破坏就只升 `GENERATOR`。

## 契约

根索引：

```json
{
  "schemaVersion": 2,
  "generator": "build_data.py 2.1.0",
  "updated": "2026-11-26T21:28:00+08:00",
  "latest": { "id": "20261126-012", "date": "2026-11-26", "project": "变形拼图（morph-puzzle）" },
  "days": [
    { "date": "2026-11-26", "weekday": "周四", "entries": 7, "sections": 5,
      "index": "data/2026-11-26/index.json", "keywords": ["evo-world", "…"] }
  ]
}
```

当日索引：

```json
{
  "schemaVersion": 2,
  "generator": "build_data.py 2.1.0",
  "date": "2026-11-26",
  "weekday": "周四",
  "entries": 7,
  "projects": [
    { "name": "演化沙盒（evo-world）", "body": "data/2026-11-26/evo-world.md",
      "entries": 3, "ids": ["20261126-007", "…"], "keywords": ["evo-world", "…"] }
  ]
}
```

正文 Markdown 的约定：

- 每条条目前面有一行 `<!-- 20261126-007 -->`，GitHub 不渲染，页面拿来当条目徽标
- 只使用：段落、空行分段、`**粗体**`、`` `代码` ``、`[文字](https://…)`、`- 列表`
- 页面先转义再做行内格式，**不接受 HTML**——数据是生成的，但外壳不该信任数据

## 缓存策略

Pages 的响应头改不了，只能靠文件名：

| 文件 | 策略 |
|---|---|
| `index.json` | 每次 `?t=<时间戳>` + `no-store` |
| `data/<date>/*` | 按日期不可变，正常缓存即可 |
| `index.html` / `assets/*` | 长期缓存；改版时改文件名或加 `?v=` |

「页面固定」换来的就是这个：外壳可以永久缓存，每天只有几百字节的根索引要重新校验。

## 生成

```bash
# 重建所有有白名单条目的天
python scripts/build_data.py

# 只重建某天
python scripts/build_data.py --date 2026-11-26

# 试跑：手工指定 id，绕开白名单（预览用）
python scripts/build_data.py --ids 20261126-001,20261126-007

# 校验现有文件与库是否仍然一致
python scripts/build_data.py --check

# 纯函数自检
python scripts/build_data.py --self-test
```

记忆库默认取仓库上一级的 `MEMORY.db`，可用 `--db` 或 `DEVLOG_DB` 覆盖。
只有列在 `entry_public` 白名单里的条目会被生成——没进白名单的一律不出现。

> 注意：试跑数据不在白名单里，`--check` 会如实报告这些「已索引但未授权」的条目。

## 本地预览

```bash
# 方式一：单文件（不需要 HTTP 服务，双击即可）
python scripts/build-preview.py

# 方式二：本地服务
python -m http.server 4310
# 打开 http://127.0.0.1:4310
```

单文件模式把 CSS/JS/全部数据塞进 `preview.html`，走 `window.__DEVLOG_FS__`；
生产路径仍然是 `fetch`，两边代码是同一份。

## 部署到 Pages

1. 仓库 Settings → Pages → Source 选分支根目录
2. 保留根目录的 `.nojekyll`
3. 免费账号只有**公开**仓库能开 Pages；私有仓库需要 GitHub Pro

## 现状

`data/2026-11-26/` 是试跑样本（`--ids` 指定），用来确认版式与格式。
真实内容要等 `entry_public` 白名单审核完，再用不带 `--ids` 的命令生成。
