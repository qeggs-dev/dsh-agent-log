#!/usr/bin/env python3
"""按规则把公开白名单里的记忆条目生成两级索引 + Markdown 正文。

    index.json                      根索引：所有天、最新条目、元信息
    data/<date>/index.json          当日索引：板块 → 正文链接 + 关键词
    data/<date>/<slug>.md           正文（Markdown）

格式全部由本脚本保证，模型只写记忆条目，不碰这些文件——这是「减少模型出错
导致格式不可解析」的做法：契约只有一处实现，且可自检。

用法：
    python scripts/build_data.py --db D:\\...\\MEMORY.db                 # 重建所有有白名单条目的天
    python scripts/build_data.py --db ... --date 2026-11-26              # 只重建某天
    python scripts/build_data.py --db ... --ids 20261126-007,20261126-009  # 手工指定（预览 / 试跑）
    python scripts/build_data.py --db ... --check                        # 只校验现有文件与库是否一致
    python scripts/build_data.py --self-test                             # 纯函数自检
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sqlite3
import sys

SCHEMA_VERSION = 2
GENERATOR = "build_data.py 2.1.0"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ROOT_INDEX = ROOT / "index.json"

# 默认读同仓上一级的记忆库；换机器用 --db 或 DEVLOG_DB 环境变量
DEFAULT_DB = os.environ.get("DEVLOG_DB") or str(ROOT.parent / "MEMORY.db")

WEEKDAYS = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")
ID_RE = re.compile(r"^[0-9]{8}-[0-9]{3}$")
ASCII_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9._-]*")


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


def entry_block(entry_id: str, content: str) -> str:
    """一条条目 → Markdown 片段。id 用 HTML 注释，GitHub 不渲染、页面拿来当徽标。"""
    body = (content or "").strip()
    return f"<!-- {entry_id} -->\n{body}\n"


def render_body(items: list[dict]) -> str:
    return "\n".join(entry_block(i["id"], i["content"]) for i in items).strip() + "\n"


def top_keywords(tags: list[str], limit: int = 6) -> list[str]:
    """标签按出现次数降序、同频按字母序，保证每次生成结果一致。"""
    counts: dict[str, int] = {}
    for t in tags:
        counts[t] = counts.get(t, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [k for k, _ in ordered[:limit]]


def day_index(date: str, projects: list[dict]) -> dict:
    total = sum(len(p["ids"]) for p in projects)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "generator": GENERATOR,
        "date": date,
        "weekday": weekday_cn(date),
        "entries": total,
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


# ---------------------------------------------------------------- 取数

def connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def fetch_rows(db_path: str, ids: list[str] | None = None) -> list[dict]:
    con = connect(db_path)
    try:
        if ids:
            # 试跑 / 预览：显式给 id，绕开白名单（仍然要求条目是 active 的）
            sql = """
                SELECT e.id, e.date, e.section_key, e.group_label, e.content, e.sort_order
                  FROM entries e
                 WHERE e.status = 'active'
                   AND e.id IN ({placeholders})
                 ORDER BY e.sort_order
            """.format(placeholders=",".join("?" * len(ids)))
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

        tag_rows = con.execute(
            "SELECT entry_id, tag FROM entry_tags ORDER BY tag"
        ).fetchall()
        tags: dict[str, list[str]] = {}
        for r in tag_rows:
            tags.setdefault(r["entry_id"], []).append(r["tag"])
        for r in rows:
            r["tags"] = tags.get(r["id"], [])
        return rows
    finally:
        con.close()


def group_by_day(rows: list[dict], slugs: dict[tuple[str, str], str] | None = None) -> dict:
    """按日期 → 板块分组。板块顺序取当天首条的 sort_order，保证稳定。"""
    days: dict[str, dict[str, list[dict]]] = {}
    for r in rows:
        name = section_name(r["section_key"], r["group_label"])
        days.setdefault(r["date"], {}).setdefault(name, []).append(r)
    return days


def build_day(date: str, sections: dict[str, list[dict]]) -> tuple[dict, dict[str, str]]:
    used: set[str] = set()
    projects, files = [], {}
    for name, items in sections.items():
        slug = slugify(name, used)
        tags = [t for i in items for t in i["tags"]]
        projects.append({
            "name": name,
            "slug": slug,
            "ids": [i["id"] for i in items],
            "keywords": top_keywords(tags),
        })
        files[f"{slug}.md"] = render_body(items)
    return day_index(date, projects), files


# ---------------------------------------------------------------- 落盘

def write_atomic(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def dump_json(path: pathlib.Path, obj: dict) -> None:
    write_atomic(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


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
        "days": days,
    }


def latest_from_rows(rows: list[dict]) -> dict | None:
    if not rows:
        return None
    r = max(rows, key=lambda x: (x["date"], x["sort_order"]))
    return {
        "id": r["id"],
        "date": r["date"],
        "project": section_name(r["section_key"], r["group_label"]),
    }


def latest_entry(db_path: str) -> dict | None:
    con = connect(db_path)
    try:
        row = con.execute("""
            SELECT e.id, e.date, e.group_label, e.section_key
              FROM entries e JOIN entry_public p ON p.entry_id = e.id
             WHERE e.status = 'active'
             ORDER BY e.date_ts DESC, e.sort_order DESC
             LIMIT 1
        """).fetchone()
    finally:
        con.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "date": row["date"],
        "project": section_name(row["section_key"], row["group_label"]),
    }


# ---------------------------------------------------------------- 命令

def cmd_build(db_path: str, date: str | None, ids: list[str] | None) -> int:
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
        index, files = build_day(day, sections)
        target = DATA_DIR / day
        for name, text in files.items():
            write_atomic(target / name, text)
        dump_json(target / "index.json", index)
        print(f"{day}: {len(index['projects'])} 个板块 / {index['entries']} 条")

    root = rebuild_root_index(db_path, dt.datetime.now().astimezone().isoformat(timespec="seconds"), rows)
    dump_json(ROOT_INDEX, root)
    print(f"index.json: {len(root['days'])} 天，最新 {root['latest']['id'] if root['latest'] else '—'}")
    return 0


def cmd_check(db_path: str) -> int:
    problems = 0
    expected = {r["id"]: r["date"] for r in fetch_rows(db_path)}
    seen: set[str] = set()

    for child in sorted(DATA_DIR.glob("*/index.json")):
        idx = json.loads(child.read_text(encoding="utf-8"))
        for project in idx["projects"]:
            body_path = ROOT / project["body"]
            if not body_path.exists():
                print(f"! {idx['date']} 缺正文 {project['body']}")
                problems += 1
                continue
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
    assert slugify("代理树", used) == "section-2", "中文名要能避免撞名"
    assert section_name("SEC:02", None) == "SEC:02"
    assert section_name("SEC:04", None) == "待办"
    assert weekday_cn("2026-11-26") == "周四"
    assert weekday_cn("2026-11-22") == "周日"

    body = render_body([
        {"id": "20261126-007", "content": "第一段\n\n第二段"},
        {"id": "20261126-009", "content": "只有一段"},
    ])
    assert body == (
        "<!-- 20261126-007 -->\n第一段\n\n第二段\n\n"
        "<!-- 20261126-009 -->\n只有一段\n"
    ), repr(body)

    assert top_keywords(["b", "a", "b"], 2) == ["b", "a"]
    assert top_keywords([], 3) == []

    idx = day_index("2026-11-26", [{
        "name": "演化沙盒 evo-world", "slug": "evo-world",
        "ids": ["20261126-007"], "keywords": ["evo"],
    }])
    assert idx["weekday"] == "周四" and idx["entries"] == 1
    assert idx["projects"][0]["body"] == "data/2026-11-26/evo-world.md", idx["projects"][0]

    print("self-test ok")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB)
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
    return cmd_build(args.db, args.date, ids)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
