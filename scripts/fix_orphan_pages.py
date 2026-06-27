#!/usr/bin/env python3
"""Regenerate pages that still point at mrakobesie.net from the fixed index.html."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "index.html"
ORPHAN_PAGES = {
    ROOT / "1714" / "index.html": "Как появились добрые сказки — Мракоборцы",
    ROOT / "1718" / "index.html": "От А до У — Мракоборцы",
}
ATTR_URL = re.compile(r'(href|src|action)=(["\'])([^"\']+)\2', re.IGNORECASE)
MRAKOBESIE = re.compile(r"^https?://(?:www\.)?mrakobesie\.net/?", re.IGNORECASE)
MIRRORED_QUERY = re.compile(
    r"<!-- Mirrored from mrakobesie\.net/\?([^ ]+) -->", re.IGNORECASE
)
REDIRECT_TARGET = re.compile(
    r'(?:Refresh" CONTENT="0; URL=|HREF=")([^">]+)', re.IGNORECASE
)


def build_query_map(root: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for stub in root.glob("index*.html"):
        if stub.name == "index.html" or not re.match(
            r"^index[a-f0-9]+\.html$", stub.name, re.I
        ):
            continue
        text = stub.read_text(encoding="utf-8", errors="replace")
        mirror = MIRRORED_QUERY.search(text)
        target = REDIRECT_TARGET.search(text)
        if not mirror or not target:
            continue
        query = unquote(mirror.group(1))
        path = unquote(target.group(1)).replace("\\", "/")
        if not path.endswith(".html"):
            path = f"{path.rstrip('/')}/index.html"
        mapping[query] = path
    return mapping


def normalize_internal_path(path: str, query_map: dict[str, str]) -> str:
    path = unquote(path.strip())
    if path.startswith("?"):
        return query_map.get(path.lstrip("?"), path)

    if path in query_map:
        return query_map[path]

    parsed = urlparse(path)
    if parsed.scheme in ("http", "https"):
        if not MRAKOBESIE.match(path):
            return path
        path = parsed.path.lstrip("/")
        if parsed.query:
            query_key = unquote(parsed.query)
            if query_key in query_map:
                return query_map[query_key]
            path = f"?{query_key}"

    if path.startswith("?"):
        return query_map.get(path.lstrip("?"), path)

    path = path.lstrip("/")
    if not path or path == "index.html":
        return "index.html"
    if path.endswith("/"):
        path = f"{path}index.html"
    elif not path.endswith(".html") and "." not in Path(path).name:
        path = f"{path}/index.html"
    return path


def prefix_url(url: str, prefix: str, query_map: dict[str, str]) -> str:
    if url.startswith(("#", "mailto:", "javascript:", "data:")):
        return url
    if url.startswith("//"):
        return url
    if url.startswith("../") or url.startswith("./"):
        return url

    lowered = url.lower()
    if lowered.startswith("http://") or lowered.startswith("https://"):
        if MRAKOBESIE.match(url):
            internal = normalize_internal_path(url, query_map)
            if internal.startswith("?"):
                return internal
            return prefix + internal.lstrip("/")
        return url

    if url.startswith("/"):
        internal = normalize_internal_path(url, query_map)
        if internal.startswith("?"):
            return internal
        return prefix + internal.lstrip("/")

    internal = normalize_internal_path(url, query_map)
    if internal.startswith("?"):
        return internal
    return prefix + internal.lstrip("/")


def adapt_for_subdirectory(content: str, prefix: str, title: str) -> str:
    query_map = build_query_map(ROOT)

    def repl(match: re.Match[str]) -> str:
        attr, quote, url = match.group(1), match.group(2), match.group(3)
        return f"{attr}={quote}{prefix_url(url, prefix, query_map)}{quote}"

    content = ATTR_URL.sub(repl, content)
    content = re.sub(
        r"<title>.*?</title>",
        f"<title>{title}</title>",
        content,
        count=1,
        flags=re.DOTALL,
    )
    content = content.replace(
        " current-menu-item current_page_item menu-item-home",
        " menu-item-home",
    )
    return content


def main() -> int:
    if not TEMPLATE.is_file():
        print(f"Missing template: {TEMPLATE}", file=sys.stderr)
        return 1

    template = TEMPLATE.read_text(encoding="utf-8", errors="replace")
    for target, title in ORPHAN_PAGES.items():
        content = adapt_for_subdirectory(template, "../", title)
        target.write_text(content, encoding="utf-8")
        print(f"Updated {target.relative_to(ROOT)}")

    for target in ORPHAN_PAGES:
        text = target.read_text(encoding="utf-8", errors="replace")
        without_comments = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        functional = ATTR_URL.sub("", without_comments)
        if "mrakobesie.net" in functional.lower():
            count = len(re.findall(r"mrakobesie\.net", functional, re.I))
            print(
                f"Warning: {target.relative_to(ROOT)} still has {count} mrakobesie.net URLs",
                file=sys.stderr,
            )
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
