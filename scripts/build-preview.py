#!/usr/bin/env python3
"""把整站打成一个单文件 preview.html：CSS/JS/全部数据/图片内联，双击即可看。

沙箱里不能监听回环端口，起不了 http.server；这个脚本产出的单文件用 file://
直接打开也能跑——文本走 window.__DEVLOG_FS__，图片就地转成 data URI。

用法：
    python scripts/build-preview.py
    python scripts/build-preview.py --self-test
"""

import base64
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}

IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
OVERVIEW_RE = re.compile(r'"overview":\s*"([^"]+)"')


def data_uri(path: pathlib.Path) -> str | None:
    mime = MIME.get(path.suffix.lower())
    if not mime or not path.is_file():
        return None
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def inline_images(text: str, base_dir: pathlib.Path) -> str:
    """Markdown 里的相对图片引用 → data URI。"""
    def repl(match: re.Match[str]) -> str:
        alt, src = match.group(1), match.group(2)
        if src.startswith("data:"):
            return match.group(0)
        uri = data_uri((base_dir / src).resolve())
        return f"![{alt}]({uri})" if uri else match.group(0)

    return IMAGE_RE.sub(repl, text)


def inline_overview(text: str) -> str:
    """当日索引里的 overview 路径 → data URI。"""
    def repl(match: re.Match[str]) -> str:
        uri = data_uri((ROOT / match.group(1)).resolve())
        return f'"overview": "{uri}"' if uri else match.group(0)

    return OVERVIEW_RE.sub(repl, text)


def bundle_js() -> str:
    """合两个 ES module：去掉 markdown.js 的 export 与 app.js 的 import。"""
    markdown = (ROOT / "assets" / "markdown.js").read_text(encoding="utf-8")
    app = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
    markdown = re.sub(r"^export\s+", "", markdown, flags=re.M)
    app = re.sub(r"^import .*?;\s*$", "", app, flags=re.M)
    return f"{markdown}\n{app}"


def collect_fs() -> dict[str, str]:
    """文本文件 → {相对路径: 内容}；图片不进来，改成引用处的 data URI。"""
    files = {"index.json": (ROOT / "index.json").read_text(encoding="utf-8")}
    search = ROOT / "search.json"
    if search.exists():
        files["search.json"] = search.read_text(encoding="utf-8")
    for path in sorted((ROOT / "data").rglob("*")):
        if not path.is_file() or path.suffix.lower() in MIME:
            continue
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".md":
            text = inline_images(text, path.parent)
        elif path.suffix == ".json":
            text = inline_overview(text)
        files[rel] = text
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
    js = bundle_js()
    assert '<link rel="stylesheet" href="assets/' not in html, "CSS 没内联"
    assert 'src="assets/app.js"' not in html, "JS 没内联"
    assert "__DEVLOG_FS__" in html, "数据没有内联"
    # 正文数据里出现 import / export 字样是正常的技术笔记，只对打包后的脚本断言
    assert "import " not in js, "ES module 的 import 没去掉"
    assert "renderMarkdown" in js and "export function" not in js, "JS 合并有问题"
    assert "resolveSrc" in js, "渲染器没有一起打包"
    # 图片必须变成 data URI，不能留相对路径（预览没有 HTTP 根）
    assert "data:image/" in html or not IMAGE_RE.search(html), "图片没有内联"
    if (ROOT / "search.json").exists():
        assert '"search.json"' in html or "search.json" in html, "搜索索引没有内联"
    print("self-test ok")


if __name__ == "__main__":
    if "--self-test" in sys.argv[1:]:
        self_test()
    else:
        target = build()
        print(f"wrote {target} ({target.stat().st_size} bytes)")
