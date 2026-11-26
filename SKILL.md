---
name: workspace-devlog
description: 维护「工作区日志」站点——把 MEMORY.db 里通过公开白名单的每日记录生成两级索引、Markdown 正文与配图，并校验/预览/发布。需要新增一天、改版式、排查站点不更新或复核公开边界时使用。
---

# 工作区日志（devlog）

一个纯静态站点：外壳固定，数据由脚本从记忆库生成。**数据文件一律不要手改**——它们
是 `scripts/build_data.py` 的产物，手改会在下次生成时被覆盖，而且绕过白名单检查。

## 结构

```
index.json                 根索引：days[] + latest（最新条目）+ search
search.json                全文搜索索引：标题 / 项目 / 关键词 / 正文（生成器全量重建）
data/<date>/index.json     当日索引：projects[] → 正文链接、ids、关键词、overview
data/<date>/<slug>.md      正文：每条一个 `## 标题`，条目 id 藏在 HTML 注释里
data/<date>/<slug>-*.png   正文配图，与 md 同目录，md 用相对路径引用
data/<date>/overview.svg   当日概览图（各板块条目数）
assets/{app.js,markdown.js,style.css}   外壳（固定，不随数据变）
scripts/build_data.py      生成器（格式契约的唯一实现）
scripts/build-preview.py   打成单文件 preview.html
tests/markdown.test.mjs    渲染器测试
```

界面是三栏：**日期 → 当日条目索引 → 单条正文**。路由 `#/<date>/<entry-id>`，
切换条目只重绘正文；`#/<date>` 落在当天第一条。左侧两栏在 ≤900px 时收成横向滚动条。

第二栏顶部有搜索框（`/` 键聚焦）。搜索是**纯前端**的：首次输入时懒加载 `search.json`，
在标题 / 项目 / 关键词 / 正文里做子串匹配，按命中位置加权排序（标题 > 关键词 > 项目 > 正文），
点结果跳到对应条目。索引由生成器每次全量重建，不需要手工维护。

## 日常：新增一天

1. 确认要发的条目已进白名单（这是唯一的授权入口）：

   ```sql
   INSERT OR IGNORE INTO entry_public(entry_id, note, approved_by, approved_at)
   VALUES ('20261126-007', '纯技术记录', 'user', '2026-11-26T21:00:00+08:00');
   ```

   `entry_public` 里没有的条目**不会**出现在站点上；撤回就是删掉那一行。

2. 生成：

   ```bash
   python scripts/build_data.py                    # 所有有白名单条目的天
   python scripts/build_data.py --date 2026-11-26  # 只重生成某天
   ```

   默认读仓库上一级的 `MEMORY.db`；换机器用 `--db <路径>` 或环境变量 `DEVLOG_DB`。

3. 校验 + 预览：

   ```bash
   python scripts/build_data.py --check          # 索引/正文/图片与库是否一致
   python scripts/build_data.py --self-test      # 纯函数自检
   node tests/markdown.test.mjs                  # 渲染器自检
   python scripts/build-preview.py               # 产出 preview.html，双击可看
   ```

4. 提交：

   ```bash
   git add -A && git commit -m "log: 2026-11-26" && git push
   ```

   Pages 会在推送后重建。**生成器和数据一起提交**——格式变更和内容变更在同一条历史里。

## 契约

根索引与当日索引都带：

- `schemaVersion`：**破坏性变更**才 +1。加一意味着 `assets/` 必须同时改，旧数据会不兼容
- `generator`：产出这批文件的脚本版本，每次实质改动都升，用于追溯

正文 Markdown 只允许这些语法（渲染器只实现这些，别指望通用 Markdown）：

| 语法 | 说明 |
|---|---|
| `## 标题` | 每条一个，渲染成 `<h4>`（页面已有 h2/h3） |
| 空行 | 分段；段内单换行渲染成 `<br>` |
| `**粗体**`、`` `代码` `` | 行内格式 |
| `[文字](https://…)` | 外链 |
| `![说明](文件名.png)` | 配图，相对路径按 md 所在目录解析 |
| `- 项目` | 无序列表 |
| `<!-- 20261126-007 -->` | 条目 id，GitHub 不渲染，页面变成条目徽标 |

## 配图规则

- 图片必须**和 md 放在同一目录**，用相对路径引用；不要外链、不要用 `/` 开头的绝对路径（Pages 子路径部署会断）
- 生成器从 `MEMORYS_ATTACHMENTS/` 复制图片过去；源目录可用 `--attachments` 指定
- 文件名冲突时自动加板块前缀；图片在 `--check` 里会验证是否存在
- 单图建议 ≤ 1 MB；`preview.html` 会把图片转成 data URI，图太大会让预览文件膨胀

## 硬规则

1. **不手改 `data/`、`index.json`**：想改内容就改记忆条目或白名单，然后重生成
2. **白名单是唯一出口**：`entry_public` 里没有那一行，就不该出现在站点上
3. **`--ids` 的产物不要提交**：它绕开了白名单，只能用于本地试跑和预览
4. **提交前扫一遍**：

   ```bash
   git grep -nIE '192\.168\.|10\.[0-9]+\.|172\.(1[6-9]|2[0-9]|3[01])\.|C:\\Users|序列号|主机名|vivo' -- data/
   ```

   应为空。命中就先处理，不要提交。
5. **改格式先想 `schemaVersion`**：破坏已发布数据就 +1，同时改 `assets/`
6. **别把站点逻辑写进生成器**：生成器只产数据，渲染逻辑在 `assets/`
7. 提交信息用 `log: <date>`（日常）或 `feat:` / `fix:`（外壳与脚本）

## 误推之后（2026-11-26 真实踩过）

用 `--ids` 的试跑数据被推到了公开仓库，里面有 VM 内网地址（`192.168.0.252`）、SSH 目标名和手机型号。要记住三件事：

- **只修 HEAD 不算修完**：删文件重新生成再提交，只影响最新提交
- **force push 不会删对象**：GitHub 仍能按旧 SHA 取到那个提交（实测 API 返回 200，patch 里原样带着内容），直到 GC。想彻底清除只能删库重建或找 GitHub Support
- 所以别指望「推错了再重写历史」——**代价最小的是推之前扫一遍**（见硬规则第 4 条）

真要清理的话：先把条目从 `entry_public` 撤下、重生成（生成器会顺带删掉该日目录里过期的文件），确认扫描干净，再考虑是否需要动历史。

## 排查

| 现象 | 先看 |
|---|---|
| 站点某天没更新 | `git log -1` 有没有推上去；Pages 部署状态；`index.json` 的 `updated` 变没变 |
| 页面空白 | 浏览器控制台；`index.json` 是否合法；`data/<date>/index.json` 的 `body` 路径 |
| 图片不显示 | md 里的相对路径是否同名文件；`--check` 会报「引用了不存在的图」 |
| 改了脚本没生效 | Pages 需要重新构建；本地 `preview.html` 要重跑 `build-preview.py` |
| `--check` 报「已索引但未授权」 | 白名单被撤了但没重生成，跑一次 `build_data.py` |

## 部署

- Settings → Pages → Source 选分支根目录；根目录保留 `.nojekyll`
- 免费账号只有**公开**仓库能开 Pages；私有仓库需要 GitHub Pro
- 沙箱环境不能监听回环端口，本地预览用 `build-preview.py` 的单文件，不要指望 `python -m http.server`
