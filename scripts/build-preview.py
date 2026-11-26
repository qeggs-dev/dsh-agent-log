#!/usr/bin/env python3
"""把整站打成一个单文件 preview.html：CSS/JS/全部数据内联，双击即可看。

沙箱里不能监听回环端口，起不了 http.server；这个脚本产出的单文件用 file://
直接打开也能跑——数据走 window.__DEVLOG_FS__，fetch 只作为生产环境的路径。

用法：
    python scripts/build-preview.py
    python scripts/build-preview.py --self-test
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def bundle_js() -> str:
    """合两个 ES module：去掉 markdown.js 的 export 与 app.js 的 import。"""
    markdown = (ROOT / "assets" / "markdown.js").read_text(encoding="utf-8")
    app = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
    markdown = re.sub(r"^export\s+", "", markdown, flags=re.M)
    app = re.sub(r"^import .*?;\s*$", "", app, flags=re.M)
    return f"{markdown}\n{app}"


def collect_fs() -> dict[str, str]:
    """整站文件 → {相对路径: 文本}，预览时顶替 HTTP。"""
    files = {"index.json": (ROOT / "index.json").read_text(encoding="utf-8")}
    for path in sorted((ROOT / "data").rglob("*")):
        if path.is_file():
            files[path.relative_to(ROOT).as_posix()] = path.read_text(encoding="utf-8")
    return files


def build() -> pathlib.Path:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
    js = bundle_js()
    files = collect_fs()

    payload = json.dumps(files, ensure_ascii=False).replace("<", "\\u003c")

    html = html.replace(
        '<link rel="stylesheet" href="assets/style.css">',
        f"<style>\n{css}\n</style>",
    )
    html = html.replace(
        '<script type="module" src="assets/app.js"></script>',
        (
            f"<script>window.__DEVLOG_FS__ = {payload};</script>\n"
            f'<script type="module">\n{js}\n</script>'
        ),
    )

    out = ROOT / "preview.html"
    out.write_text(html, encoding="utf-8")
    return out


def self_test() -> None:
    html = build().read_text(encoding="utf-8")
    assert "assets/" not in html, "还有外链资源没内联"
    assert "__DEVLOG_FS__" in html, "数据没有内联"
    assert "import {" not in html, "ES module 的 import 没去掉"
    assert "renderMarkdown" in html and "export function" not in html, "JS 合并有问题"
    assert '"data/2026-11-26/' in html or "data/" in html, "没有数据文件"
    print("self-test ok")


if __name__ == "__main__":
    if "--self-test" in sys.argv[1:]:
        self_test()
    else:
        target = build()
        print(f"wrote {target} ({target.stat().st_size} bytes)")
