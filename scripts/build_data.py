#!/usr/bin/env python3
"""按规则把公开白名单里的记忆条目生成两级索引 + Markdown 正文 + 配图。

    index.json                      根索引：所有天、最新条目、元信息
    data/<date>/index.json          当日索引：板块 → 正文链接 + 关键词 + 概览图
    data/<date>/<slug>.md           正文（Markdown，带条目标题）
    data/<date>/<slug>-n.png        该板块的配图（与正文同目录，相对链接引用）
    data/<date>/overview.svg        当日概览图（条目分布）

格式全部由本脚本保证，模型只写记忆条目，不碰这些文件——契约只有一处实现，
且可自检。图片一律复制到正文旁边，Markdown 用相对路径引用（仓库内自包含）。

用法：
    python scripts/build_data.py --db ../MEMORY.db
    python scripts/build_data.py --date 2026-11-26
    python scripts/build_data.py --ids 20261126-007,20261126-009     # 试跑，绕开白名单
    python scripts/build_data.py --check
    python scripts/build_data.py --self-test
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import pathlib
import re
import shutil
import sqlite3
import sys

SCHEMA_VERSION = 4
GENERATOR = "build_data.py 3.1.0"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ROOT_INDEX = ROOT / "index.json"
SEARCH_INDEX = ROOT / "search.json"
SEARCH_EXCERPT = 4000

# 默认读同仓上一级的记忆库；换机器用 --db 或 DEVLOG_DB
DEFAULT_DB = os.environ.get("DEVLOG_DB") or str(ROOT.parent / "MEMORY.db")
DEFAULT_ATTACHMENTS = str(ROOT.parent / "MEMORYS_ATTACHMENTS")

WEEKDAYS = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")
ID_RE = re.compile(r"^[0-9]{8}-[0-9]{3}$")
ID_LINE_RE = re.compile(r"^<!--\s*([0-9]{8}-[0-9]{3})\s*-->$", re.M)
ASCII_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9._-]*")
BOLD_LEAD_RE = re.compile(r"^\*\*(.+?)\*\*\s*[：:]?\s*", re.S)
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")


# ---------------------------------------------------------------- 纯函数

def weekday_cn(date: str) -> str:
    return WEEKDAYS[dt.date.fromisoformat(date).weekday()]


def slugify(name: str, used: set[str]) -> str:
    """项目名 → 文件名。取名字里的 ASCII 词，中文名退化到 section-N。"""
    tokens = ASCII_TOKEN_RE.findall(name or "")
    base = re.sub(r"[^a-z0-9._-]+", "-", "-".join(t.lower() for t in tokens)).strip("-")
    base = base or "section"
    slug, n = base, 2
    while slug in used:
        slug = f"{base}-{n}"
        n += 1
    used.add(slug)
    return slug


def section_name(section_key: str, group_label: str | None) -> str:
    if group_label:
        return group_label
    return {"SEC:03": "决策", "SEC:04": "待办"}.get(section_key, section_key)


def _strip_lead(text: str) -> str:
    """去掉标题后面残留的句号 / 冒号 / 空白。"""
    return text.lstrip().lstrip("。：:").strip()


def split_title(content: str) -> tuple[str, str]:
    """从正文里取一条标题：`**…**：` 开头优先，其次是「前缀：」结构，最后退回首句。

    返回 (标题, 去掉标题前缀后的正文)；正文不会丢内容，截断只在最后一种情况发生。
    """
    text = (content or "").strip()

    m = BOLD_LEAD_RE.match(text)
    if m and len(m.group(1)) <= 80:
        title = m.group(1).strip().rstrip("：:").strip()
        if title:
            return title, _strip_lead(text[m.end():])

    # 冒号前缀只在第一句之内成立，避免把「A。B：C」当成标题
    head = re.split(r"[。\n]", text, 1)[0]
    colon = re.search(r"[：:]", head[:40])
    if colon:
        title = head[:colon.start()].strip()
        if 2 <= len(title) <= 48:
            return title, _strip_lead(text[colon.end():])

    first = re.split(r"[。\n]", text, 1)[0]
    if len(first) <= 40:
        return first.strip(), text[len(first):].lstrip("。\n ").strip()
    return text[:32].strip() + "…", text


def top_keywords(tags: list[str], limit: int = 6) -> list[str]:
    """标签按出现次数降序、同频按字母序，保证每次生成结果一致。"""
    counts: dict[str, int] = {}
    for t in tags:
        counts[t] = counts.get(t, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [k for k, _ in ordered[:limit]]


LABEL_RE = re.compile(
    r"^\*\*(?P<label>[^*\n]{2,18})\*\*\s*(?:（(?P<note>[^）]{0,40})）)?\s*[：:]\s*"
)
PLAIN_LABEL_RE = re.compile(r"^(?P<label>[A-Za-z\u4e00-\u9fff][A-Za-z0-9\u4e00-\u9fff_-]{1,7})[：:]\s*")
BAD_LABEL_CHARS = "/\\.…*（）()`"


def take_label(sentence: str) -> tuple[str | None, str]:
    """句首的 `**小标题**：` 或 `短标签：` → (标签, 正文)；不像标签就返回 (None, 原句)。"""
    for rx in (LABEL_RE, PLAIN_LABEL_RE):
        m = rx.match(sentence)
        if not m:
            continue
        label = m.group("label").strip()
        note = (m.groupdict().get("note") or "").strip()
        rest = sentence[m.end():].strip()
        if len(rest) < 8 or not label:
            continue
        if any(ch in label for ch in BAD_LABEL_CHARS):
            continue
        if label[0] in "①②③④⑤⑥⑦⑧⑨⑩":
            continue
        body = f"{note}：{rest}" if note else rest
        return label, body
    return None, sentence


def reflow(text: str, width: int = 160) -> str:
    """把堆成一行的长段落重新分段、并把句首小标题提升成 `### 标题`（只排版，不改字）。"""
    out = []
    for para in (p.strip() for p in re.split(r"\n{2,}", text)):
        if not para:
            continue
        if "\n" in para:  # 已经是多行的段落不重排，避免破坏作者自己的换行
            out.append(para)
            continue
        buf = ""
        for sent in re.findall(r"[^。！？；]*[。！？；]?", para):
            if not sent.strip():
                continue
            label, rest = take_label(sent.strip())
            if label:
                if buf:
                    out.append(buf)
                out.append(f"### {label}")
                buf = rest
            elif buf and len(buf) + len(sent) > width:
                out.append(buf)
                buf = sent
            else:
                buf += sent
        if buf:
            out.append(buf)
    return "\n\n".join(out)


# 本机路径 / 环境相关前缀 → 通用占位符（保留有用的相对部分，去掉机器信息）
PATH_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"[A-Za-z]:\\Projects\\Deepseek_Harness_Workspace", re.I), "〈工作区〉"),
    (re.compile(r"[A-Za-z]:\\Projects\\DSH_Normal_Workspace", re.I), "〈第二工作区〉"),
    (re.compile(r"[A-Za-z]:\\Projects\\", re.I), "〈项目目录〉/"),
    (re.compile(r"[A-Za-z]:\\Interesting_projects\\", re.I), "〈源码目录〉/"),
    (re.compile(r"[A-Za-z]:\\work\\projects\\", re.I), "〈项目目录〉/"),
    (re.compile(r"[A-Za-z]:\\work\\", re.I), "〈工作目录〉/"),
    (re.compile(r"[A-Za-z]:\\Deepseek_Harness_Temp", re.I), "〈临时目录〉"),
    (re.compile(r"[A-Za-z]:\\Temp(?=[\\\s`'\"]|$)", re.I), "〈临时目录〉"),
    (re.compile(r"[A-Za-z]:\\Users\\[^\\\s`'\"]+", re.I), "〈用户目录〉"),
    (re.compile(r"[A-Za-z]:\\Apps\\", re.I), "〈安装目录〉/"),
    (re.compile(r"[A-Za-z]:\\Program Files(?: \(x86\))?\\", re.I), "〈安装目录〉/"),
    (re.compile(r"[A-Za-z]:\\Windows\\", re.I), "〈系统目录〉/"),
    (re.compile(r"[A-Za-z]:\\[^\s`'\"()<>|，。；：]*"), "〈本机路径〉"),
    (re.compile(r"~[/\\]"), "〈用户目录〉/"),
]

TOKEN_PATH = re.compile(r"(〈[^〉]+〉[^\s`'\"()<>|，。；：]*)")


def _slash(match: re.Match[str]) -> str:
    return match.group(1).replace("\\", "/")


def sanitize(text: str) -> str:
    """去掉本机特定路径，只留能公开的部分。

    已知前缀换成占位符并保留相对路径（`〈工作区〉/evo-world/`），
    其余盘符路径一律换成 `〈本机路径〉`；`~/` 换成 `〈用户目录〉/`。
    """
    out = text
    for pattern, repl in PATH_RULES:
        out = pattern.sub(repl, out)
    return TOKEN_PATH.sub(_slash, out)


def entry_block(item: dict, images: list[str]) -> str:
    """一条条目 → Markdown：隐藏的 id 注释 + 正文 + 相对链接的配图。

    标题只从 `item["title"]`（数据通道）取，不从正文里解析；
    这里仍写一行 `## 标题` 只是为了在 GitHub 上直接读 md 时有层次。
    """
    title = item.get("title") or ""
    body = item.get("body") or ""
    parts = [f"<!-- {item['id']} -->"]
    if title:
        parts.append(f"## {title}")
    if body:
        parts.append(reflow(body))
    for alt, rel in images:
        parts.append(f"![{alt}]({rel})")
    return "\n\n".join(parts)


def render_body(items: list[dict]) -> str:
    blocks = [entry_block(i, i.get("images", [])) for i in items]
    return "\n\n".join(blocks).strip() + "\n"


def day_index(date: str, projects: list[dict], items: list[dict]) -> dict:
    total = sum(len(p["ids"]) for p in projects)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "generator": GENERATOR,
        "date": date,
        "weekday": weekday_cn(date),
        "entries": total,
        "overview": f"data/{date}/overview.svg",
        "items": [
            {"id": i["id"], "title": i["title"], "project": i["project"]} for i in items
        ],
        "projects": [
            {
                "name": p["name"],
                "body": f"data/{date}/{p['slug']}.md",
                "entries": len(p["ids"]),
                "ids": p["ids"],
                "keywords": p["keywords"],
            }
            for p in projects
        ],
    }


# ---------------------------------------------------------------- 概览图

OVERVIEW_W = 360
OVERVIEW_LABEL = 150
OVERVIEW_ROW = 22
OVERVIEW_TOP = 8


def overview_svg(date: str, projects: list[dict]) -> str:
    """当日概览：每个板块一条横杠，长度=条目数。宽度按侧栏第二列设计。"""
    height = OVERVIEW_TOP + OVERVIEW_ROW * max(len(projects), 1) + 10
    total = sum(p["entries"] for p in projects)
    max_n = max((p["entries"] for p in projects), default=1)
    bar_max = OVERVIEW_W - OVERVIEW_LABEL - 46

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{OVERVIEW_W}" height="{height}" '
        f'viewBox="0 0 {OVERVIEW_W} {height}" role="img" '
        f'font-family="system-ui, -apple-system, Segoe UI, Microsoft YaHei, sans-serif">',
    ]
    for i, p in enumerate(projects):
        y = OVERVIEW_TOP + i * OVERVIEW_ROW
        name = p["name"] if len(p["name"]) <= 16 else p["name"][:15] + "…"
        width = max(4, round(bar_max * p["entries"] / max_n))
        out.append(
            f'<text x="0" y="{y + 11}" font-size="10" fill="#8a7a64">'
            f'{html.escape(name)}</text>'
        )
        out.append(
            f'<rect x="{OVERVIEW_LABEL}" y="{y + 3}" width="{width}" height="9" rx="4" '
            f'fill="#e8a800" opacity="0.7"/>'
        )
        out.append(
            f'<text x="{OVERVIEW_LABEL + width + 6}" y="{y + 12}" font-size="10" '
            f'fill="#b3a48c">{p["entries"]} 条</text>'
        )
    out.append("</svg>")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- 取数

def connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def fetch_rows(db_path: str, ids: list[str] | None = None) -> list[dict]:
    con = connect(db_path)
    try:
        if ids:
            # 试跑 / 预览：显式给 id，绕开白名单（仍要求条目 active）
            sql = """
                SELECT e.id, e.date, e.section_key, e.group_label, e.content, e.sort_order
                  FROM entries e
                 WHERE e.status = 'active' AND e.id IN ({ph})
                 ORDER BY e.sort_order
            """.format(ph=",".join("?" * len(ids)))
            rows = [dict(r) for r in con.execute(sql, ids)]
        else:
            sql = """
                SELECT e.id, e.date, e.section_key, e.group_label, e.content, e.sort_order
                  FROM entries e
                  JOIN entry_public p ON p.entry_id = e.id
                 WHERE e.status = 'active'
                 ORDER BY e.sort_order
            """
            rows = [dict(r) for r in con.execute(sql)]

        tags: dict[str, list[str]] = {}
        for r in con.execute("SELECT entry_id, tag FROM entry_tags ORDER BY tag"):
            tags.setdefault(r["entry_id"], []).append(r["tag"])
        images: dict[str, list[dict]] = {}
        for r in con.execute(
            "SELECT entry_id, path, description FROM attachments "
            "WHERE status = 'active' ORDER BY sort_order"
        ):
            if r["path"].lower().endswith(IMAGE_EXT):
                images.setdefault(r["entry_id"], []).append(
                    {"path": r["path"], "description": r["description"] or ""}
                )
        for r in rows:
            r["tags"] = tags.get(r["id"], [])
            r["attachments"] = images.get(r["id"], [])
        return rows
    finally:
        con.close()


def group_by_day(rows: list[dict]) -> dict[str, dict[str, list[dict]]]:
    days: dict[str, dict[str, list[dict]]] = {}
    for r in rows:
        name = section_name(r["section_key"], r["group_label"])
        days.setdefault(r["date"], {}).setdefault(name, []).append(r)
    return days


def build_day(date: str, sections: dict[str, list[dict]], attachments_root: pathlib.Path,
              copies: list[tuple[pathlib.Path, pathlib.Path]]) -> tuple[dict, dict[str, str]]:
    """返回 (当日索引, {文件名: 文本})；需要复制的图片追加进 copies。"""
    used_slugs: set[str] = set()
    used_files: set[str] = set()
    projects, files, items_meta = [], {}, []

    for name, items in sections.items():
        slug = slugify(name, used_slugs)
        for item in items:
            item["images"] = []
            for att in item["attachments"]:
                src = attachments_root / att["path"]
                if not src.exists():
                    continue
                filename = src.name
                if filename in used_files:
                    filename = f"{slug}-{filename}"
                used_files.add(filename)
                dst = DATA_DIR / date / filename
                copies.append((src, dst))
                item["images"].append((att["description"] or "配图", filename))

            item["title"], item["body"] = split_title(sanitize(item["content"]))
            items_meta.append({"id": item["id"], "title": item["title"], "project": name})

        tags = [t for i in items for t in i["tags"]]
        projects.append({
            "name": name,
            "slug": slug,
            "ids": [i["id"] for i in items],
            "keywords": top_keywords(tags),
        })
        files[f"{slug}.md"] = render_body(items)

    index = day_index(date, projects, items_meta)
    files["overview.svg"] = overview_svg(
        date, [{"name": p["slug"], "entries": len(p["ids"])} for p in projects]
    )
    return index, files


# ---------------------------------------------------------------- 落盘

def write_atomic(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def dump_json(path: pathlib.Path, obj: dict) -> None:
    write_atomic(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def copy_file(src: pathlib.Path, dst: pathlib.Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.name + ".tmp")
    shutil.copyfile(src, tmp)
    os.replace(tmp, dst)


def rebuild_root_index(db_path: str, now: str, rows: list[dict] | None = None) -> dict:
    days = []
    for child in sorted(DATA_DIR.glob("*/index.json")):
        idx = json.loads(child.read_text(encoding="utf-8"))
        all_kw = [k for p in idx["projects"] for k in p["keywords"]]
        days.append({
            "date": idx["date"],
            "weekday": idx["weekday"],
            "entries": idx["entries"],
            "sections": len(idx["projects"]),
            "index": f"data/{idx['date']}/index.json",
            "keywords": top_keywords(all_kw, 10),
        })
    days.sort(key=lambda d: d["date"], reverse=True)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "generator": GENERATOR,
        "updated": now,
        "latest": latest_from_rows(rows) if rows else (latest_entry(db_path) if days else None),
        "search": "search.json",
        "days": days,
    }


def latest_from_rows(rows: list[dict]) -> dict | None:
    if not rows:
        return None
    r = max(rows, key=lambda x: (x["date"], x["sort_order"]))
    return {"id": r["id"], "date": r["date"],
            "project": section_name(r["section_key"], r["group_label"])}


def latest_entry(db_path: str) -> dict | None:
    con = connect(db_path)
    try:
        row = con.execute("""
            SELECT e.id, e.date, e.group_label, e.section_key
              FROM entries e JOIN entry_public p ON p.entry_id = e.id
             WHERE e.status = 'active'
             ORDER BY e.date_ts DESC, e.sort_order DESC LIMIT 1
        """).fetchone()
    finally:
        con.close()
    if not row:
        return None
    return {"id": row["id"], "date": row["date"],
            "project": section_name(row["section_key"], row["group_label"])}


# ---------------------------------------------------------------- 命令

def cmd_build(db_path: str, date: str | None, ids: list[str] | None,
              attachments_root: pathlib.Path) -> int:
    rows = fetch_rows(db_path, ids)
    if not rows:
        print("库里没有可公开的条目（entry_public 为空？）", file=sys.stderr)
        return 1

    by_day = group_by_day(rows)
    if date:
        by_day = {d: v for d, v in by_day.items() if d == date}
        if not by_day:
            print(f"{date} 没有可公开的条目", file=sys.stderr)
            return 1

    for day, sections in sorted(by_day.items()):
        copies: list[tuple[pathlib.Path, pathlib.Path]] = []
        index, files = build_day(day, sections, attachments_root, copies)
        target = DATA_DIR / day
        for name, text in files.items():
            write_atomic(target / name, text)
        for src, dst in copies:
            copy_file(src, dst)
        dump_json(target / "index.json", index)

        # 重生成会清掉该日目录里不再属于本次输出的文件（撤销白名单后不留残影）
        keep = set(files) | {dst.name for _, dst in copies} | {"index.json"}
        for stale in target.iterdir():
            if stale.is_file() and stale.name not in keep:
                stale.unlink()

        print(f"{day}: {len(index['projects'])} 个板块 / {index['entries']} 条 / "
              f"{len(copies)} 张图")

    root = rebuild_root_index(db_path, dt.datetime.now().astimezone().isoformat(timespec="seconds"), rows)
    dump_json(ROOT_INDEX, root)
    print(f"index.json: {len(root['days'])} 天，最新 {root['latest']['id'] if root['latest'] else '—'}")

    search = rebuild_search_index(root["updated"])
    dump_json(SEARCH_INDEX, search)
    print(f"search.json: {search['count']} 条")
    return 0


def iter_md_items(text: str) -> list[tuple[str, str]]:
    """按 `<!-- id -->` 把一份正文切成 (id, 正文块)。"""
    parts = ID_LINE_RE.split(text)
    return [(parts[i], parts[i + 1].strip()) for i in range(1, len(parts) - 1, 2)]


def item_title_body(block: str) -> tuple[str, str]:
    """正文块 → (标题, 去掉标题行的正文)。"""
    lines = block.split("\n")
    if lines and lines[0].startswith("## "):
        return lines[0][3:].strip(), "\n".join(lines[1:]).strip()
    return split_title(block)


def rebuild_search_index(now: str) -> dict:
    """全量重建 search.json：标题 / 项目 / 关键词 / 正文摘要，供前端本地搜索。"""
    entries = []
    for child in sorted(DATA_DIR.glob("*/index.json"), reverse=True):
        idx = json.loads(child.read_text(encoding="utf-8"))
        titles = {e["id"]: e.get("title", "") for e in idx.get("items", [])}
        for project in idx["projects"]:
            body_path = ROOT / project["body"]
            if not body_path.exists():
                continue
            for item_id, block in iter_md_items(body_path.read_text(encoding="utf-8")):
                fallback, rest = item_title_body(block)
                title = titles.get(item_id) or fallback
                entries.append({
                    "d": idx["date"],
                    "i": item_id,
                    "p": project["name"],
                    "t": title,
                    "k": project.get("keywords", [])[:6],
                    "x": re.sub(r"\s+", " ", rest)[:SEARCH_EXCERPT],
                })
    return {
        "schemaVersion": SCHEMA_VERSION,
        "generator": GENERATOR,
        "updated": now,
        "count": len(entries),
        "entries": entries,
    }


def cmd_check(db_path: str) -> int:
    problems = 0
    expected = {r["id"]: r["date"] for r in fetch_rows(db_path)}
    seen: set[str] = set()

    for child in sorted(DATA_DIR.glob("*/index.json")):
        idx = json.loads(child.read_text(encoding="utf-8"))
        overview = ROOT / idx.get("overview", "")
        if idx.get("overview") and not overview.exists():
            print(f"! {idx['date']} 缺概览图 {idx['overview']}")
            problems += 1
        for project in idx["projects"]:
            body_path = ROOT / project["body"]
            if not body_path.exists():
                print(f"! {idx['date']} 缺正文 {project['body']}")
                problems += 1
                continue
            text = body_path.read_text(encoding="utf-8")
            for match in re.finditer(r"!\[[^\]]*\]\(([^)\s]+)\)", text):
                image = (body_path.parent / match.group(1)).resolve()
                if not image.exists():
                    print(f"! {project['body']} 引用了不存在的图 {match.group(1)}")
                    problems += 1
            for entry_id in project["ids"]:
                seen.add(entry_id)
                if entry_id not in expected:
                    print(f"! {entry_id} 在 {project['body']} 里，但已不在白名单")
                    problems += 1
                elif expected[entry_id] != idx["date"]:
                    print(f"! {entry_id} 日期不符：索引 {idx['date']} / 库 {expected[entry_id]}")
                    problems += 1

    for entry_id in sorted(set(expected) - seen):
        print(f"! {entry_id} 在白名单里，但没有出现在任何索引")
        problems += 1

    print(f"check: {len(seen)} 条被索引，{problems} 个问题")
    return 0 if problems == 0 else 2


# ---------------------------------------------------------------- 自检

def self_test() -> int:
    used: set[str] = set()
    assert slugify("演化沙盒 evo-world", used) == "evo-world"
    assert slugify("DSH 插件：图片差异对比（image-delta）", used) == "dsh-image-delta"
    assert slugify("代理树", used) == "section"
    assert slugify("代理树", used) == "section-2"
    assert section_name("SEC:02", None) == "SEC:02"
    assert section_name("SEC:04", None) == "待办"
    assert weekday_cn("2026-11-26") == "周四"

    # 标题提升
    assert split_title("**新建并安装**：正文内容") == ("新建并安装", "正文内容")
    assert split_title("**v3 改成两界（2026-11-26，取代三界版）**。后面")[0] == "v3 改成两界（2026-11-26，取代三界版）"
    short, rest = split_title("短句。后面还有")
    assert short == "短句" and rest == "后面还有", (short, rest)
    long_title, long_rest = split_title("啊" * 60)
    assert long_title.endswith("…") and long_rest == "啊" * 60
    # 「前缀：正文」结构，前缀当标题、正文不重复前缀
    assert split_title("dsh-desktop-shell：把 dsh web 装进窗口") == (
        "dsh-desktop-shell", "把 dsh web 装进窗口")
    # 标题后面残留的句号要去掉
    assert split_title("**标题**。正文") == ("标题", "正文")
    # 冒号不能跨句：句号之后的前缀不算
    assert split_title("Android 壳阶段 A/B 通过。APK：路径") == (
        "Android 壳阶段 A/B 通过", "APK：路径")

    # 条目块：标题来自数据字段，不解析正文
    block = entry_block({"id": "20261126-007", "title": "标题", "body": "正文"},
                        [("截图", "evo-1.png")])
    assert block.startswith("<!-- 20261126-007 -->"), block
    assert "\n## 标题\n" in block
    assert "![截图](evo-1.png)" in block

    body = render_body([
        {"id": "20261126-007", "title": "一", "body": "甲"},
        {"id": "20261126-009", "title": "二", "body": "乙"},
    ])
    assert body.count("<!--") == 2 and "## 一" in body and "## 二" in body

    # 概览图：转义 + 条数
    svg = overview_svg("2026-11-26", [
        {"name": "a<b", "entries": 2}, {"name": "中文板块", "entries": 1}])
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    assert "a&lt;b" in svg and "2 条" in svg

    # 索引字段：标题走独立的数据通道
    idx = day_index("2026-11-26", [{"name": "p", "slug": "p", "ids": ["20261126-007"],
                                    "keywords": ["k"]}],
                    [{"id": "20261126-007", "title": "标题", "project": "p"}])
    assert idx["schemaVersion"] == SCHEMA_VERSION
    assert idx["overview"] == "data/2026-11-26/overview.svg"
    assert idx["projects"][0]["body"] == "data/2026-11-26/p.md"
    assert idx["items"] == [{"id": "20261126-007", "title": "标题", "project": "p"}]

    # 搜索索引的切块
    md = ("<!-- 20261126-001 -->\n\n## 标题一\n\n正文一\n\n"
          "<!-- 20261126-002 -->\n\n## 标题二\n\n正文二\n")
    items = iter_md_items(md)
    assert [i for i, _ in items] == ["20261126-001", "20261126-002"], items
    assert item_title_body(items[0][1]) == ("标题一", "正文一"), item_title_body(items[0][1])

    # 长段落重排：只加换行、不改字
    assert reflow("短句。") == "短句。"
    long_para = "甲" * 100 + "。" + "乙" * 100 + "。" + "丙" * 100 + "。"
    parts = reflow(long_para).split("\n\n")
    assert len(parts) >= 2 and "".join(parts) == long_para, parts
    # 句首小标题提升成独立的 ### 标题
    assert reflow("前一句。**实测**：这是足够长的正文内容，用来验证标题提升。") == (
        "前一句。\n\n### 实测\n\n这是足够长的正文内容，用来验证标题提升。"
    )
    label, body = take_label("**实测**（宿主内）：这里是一段足够长的正文内容。")
    assert label == "实测" and body.startswith("宿主内："), (label, body)
    assert take_label("普通的一句话，没有标签。")[0] is None

    # 本机路径脱敏：去掉机器信息、保留能公开的相对部分
    assert sanitize(r"落在 D:\Projects\Deepseek_Harness_Workspace\evo-world\ 里") == (
        "落在 〈工作区〉/evo-world/ 里"
    )
    assert sanitize(r"`C:\Users\Administrator-Local\.dsh\x`") == "`〈用户目录〉/.dsh/x`"
    assert sanitize("见 ~/.ssh/id_ed25519") == "见 〈用户目录〉/.ssh/id_ed25519"
    assert sanitize(r"R:\Temp") == "〈临时目录〉"
    assert sanitize(r"装在 D:\Apps\Adobe\Pr") == "装在 〈安装目录〉/Adobe/Pr"
    assert sanitize(r"奇怪的位置 E:\somewhere\x") == "奇怪的位置 〈本机路径〉"

    print("self-test ok")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--attachments", default=DEFAULT_ATTACHMENTS)
    ap.add_argument("--date")
    ap.add_argument("--ids")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    ids = [i.strip() for i in args.ids.split(",") if i.strip()] if args.ids else None
    if ids:
        bad = [i for i in ids if not ID_RE.match(i)]
        if bad:
            print(f"id 格式不对：{bad}", file=sys.stderr)
            return 1
    if args.check:
        return cmd_check(args.db)
    return cmd_build(args.db, args.date, ids, pathlib.Path(args.attachments))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
