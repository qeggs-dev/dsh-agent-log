# 工作区日志

固定外壳 + 两级索引 + Markdown 正文与配图。页面写一次不再动，每天只多一个数据目录。

```
index.json                        根索引：所有天、最新条目、元信息
data/<date>/index.json            当日索引：板块 → 正文链接 + 关键词 + 概览图
data/<date>/<slug>.md             正文（每条一个标题，GitHub 上也能直接读）
data/<date>/<slug>-*.png          正文配图（与 md 同目录，相对路径引用）
data/<date>/overview.svg          当日概览图

index.html                        外壳
assets/app.js                     读索引 → 读正文 → 渲染
assets/markdown.js                只渲染生成器会产出的 Markdown 子集
assets/style.css                  样式（跟随系统深浅色）

scripts/build_data.py             生成器：MEMORY.db → 上述数据
scripts/build-preview.py          把整站打成单文件 preview.html

tests/markdown.test.mjs           渲染器测试
SKILL.md                          操作手册（给 agent 看的：怎么加一天、怎么排错）
```

## 为什么生成器在仓库里

数据是生成的，**生成器就是格式契约的唯一实现**。它和数据在同一个仓库、同一条历史里：
哪天格式变了，`git log` 能同时看到「改了脚本」和「从哪天起数据长这样」。

每份产物都带版本戳：

```json
{ "schemaVersion": 4, "generator": "build_data.py 3.0.0" }
```

- `schemaVersion` 只在**破坏性变更**时加一——加一意味着外壳必须同时改
- `generator` 每次实质性改动都升——同一份 `schemaVersion` 下也能追溯出处

## 契约

根索引：

```json
{
  "schemaVersion": 4,
  "generator": "build_data.py 3.0.0",
  "updated": "2026-11-26T21:34:00+08:00",
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
  "schemaVersion": 4,
  "generator": "build_data.py 3.0.0",
  "date": "2026-11-26",
  "weekday": "周四",
  "entries": 7,
  "overview": "data/2026-11-26/overview.svg",
  "items": [{ "id": "20261126-007", "title": "演化沙盒 evo-world 新建", "project": "演化沙盒（evo-world）" }],
  "projects": [
    { "name": "演化沙盒（evo-world）", "body": "data/2026-11-26/evo-world.md",
      "entries": 3, "ids": ["20261126-007", "…"], "keywords": ["evo-world", "…"] }
  ]
}
```

正文 Markdown 只使用这些语法（渲染器只实现这些）：

| 语法 | 说明 |
|---|---|
| `## 标题` | 每条一个，渲染成 `<h4>` |
| 空行 / 单换行 | 分段 / 段内 `<br>` |
| `**粗体**`、`` `代码` `` | 行内格式 |
| `[文字](https://…)` | 外链 |
| `![说明](文件名.png)` | 配图，相对路径按 md 所在目录解析 |
| `### 小标题` | 条目内的分节，渲染成 `<h5>`；生成器会把句首的 `**实测**：` / `形态：` 这类提升成它 |
| `- 项目` | 无序列表 |
| `<!-- 20261126-007 -->` | 条目 id，GitHub 不渲染，页面当徽标 |

页面**先转义再格式化**，不接受 HTML——外壳不该信任数据。

## 图片

- 图片必须和 md **放在同一目录**，用相对路径引用（外链和 `/` 开头都会在 Pages 子路径下断掉）
- 生成器按条目的 `attachments` 复制图片进来，文件名冲突时加板块前缀
- `--check` 会验证 md 引用的图片是否真的存在
- `preview.html` 会把图片内联成 data URI，所以别放太大的图（单图 ≤ 1 MB 比较合适）

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
python scripts/build_data.py                     # 重建所有有白名单条目的天
python scripts/build_data.py --date 2026-11-26   # 只重建某天
python scripts/build_data.py --ids 20261126-007  # 试跑：绕开白名单
python scripts/build_data.py --check             # 校验文件与库是否一致
python scripts/build_data.py --self-test
```

记忆库默认取仓库上一级的 `MEMORY.db`，可用 `--db` 或 `DEVLOG_DB` 覆盖；附件目录用
`--attachments` 指定。只有列在 `entry_public` 白名单里的条目会被生成。

> 注意：试跑数据不在白名单里，`--check` 会如实报告这些「已索引但未授权」的条目。

## 本地预览

```bash
python scripts/build-preview.py     # 单文件，双击即可（沙箱里起不了 HTTP 服务）
python -m http.server 4310          # 或者起本地服务
```

单文件模式把 CSS/JS/数据/图片塞进 `preview.html`，文本走 `window.__DEVLOG_FS__`；
生产路径仍然是 `fetch`，两边代码是同一份。

## 部署到 Pages

1. 仓库 Settings → Pages → Source 选分支根目录
2. 保留根目录的 `.nojekyll`
3. 免费账号只有**公开**仓库能开 Pages；私有仓库需要 GitHub Pro

## 现状

`data/` 里的两天是试跑样本（`--ids` 指定），用来确认版式、图片与格式。
真实内容要等 `entry_public` 白名单审核完，再用不带 `--ids` 的命令生成。
