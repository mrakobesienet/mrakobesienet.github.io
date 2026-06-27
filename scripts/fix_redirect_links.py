#!/usr/bin/env python3
"""Replace HTTrack WordPress redirect stub links with canonical relative URLs."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
REDIRECT_STUB = re.compile(r"^index[a-f0-9]+\.html$", re.IGNORECASE)
REDIRECT_TARGET = re.compile(r'(?:Refresh" CONTENT="0; URL=|HREF=")([^">]+)', re.IGNORECASE)
LINK_PATTERN = re.compile(
    r'((?:\.\./)*)index([a-f0-9]+)\.html\?[^"\'>\s]+',
    re.IGNORECASE,
)


def build_redirect_map(root: Path) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    missing: list[str] = []

    for stub in sorted(root.glob("index*.html")):
        if stub.name == "index.html" or not REDIRECT_STUB.match(stub.name):
            continue
        text = stub.read_text(encoding="utf-8", errors="replace")
        match = REDIRECT_TARGET.search(text)
        if not match:
            continue
        target_rel = unquote(match.group(1)).replace("\\", "/")
        target = (root / target_rel).resolve()
        if not target.is_file():
            missing.append(f"{stub.name} -> {target_rel}")
            continue
        mapping[stub.name.lower()] = target

    if missing:
        print("Warning: unresolved redirect targets:", file=sys.stderr)
        for item in missing:
            print(f"  {item}", file=sys.stderr)

    return mapping


def relative_href(from_file: Path, target: Path) -> str:
    if from_file.resolve() == target.resolve():
        return "index.html"
    return Path(os_path_relpath(target, from_file.parent)).as_posix()


def os_path_relpath(target: Path, start: Path) -> str:
    return os.path.relpath(target, start)


def fix_file(path: Path, redirects: dict[str, Path]) -> int:
    content = path.read_text(encoding="utf-8", errors="replace")
    replacements = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal replacements
        stub = f"index{match.group(2)}.html".lower()
        target = redirects.get(stub)
        if target is None:
            return match.group(0)
        replacements += 1
        return relative_href(path, target)

    new_content = LINK_PATTERN.sub(repl, content)
    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
    return replacements


def main() -> int:
    redirects = build_redirect_map(ROOT)
    print(f"Loaded {len(redirects)} redirect mappings")

    total_files = 0
    total_links = 0
    remaining = 0

    for html in ROOT.rglob("*.html"):
        if html.parent == ROOT and REDIRECT_STUB.match(html.name):
            continue
        count = fix_file(html, redirects)
        if count:
            total_files += 1
            total_links += count

    for html in ROOT.rglob("*.html"):
        if html.parent == ROOT and REDIRECT_STUB.match(html.name):
            continue
        remaining += len(LINK_PATTERN.findall(html.read_text(encoding="utf-8", errors="replace")))

    print(f"Updated {total_links} links in {total_files} files")
    if remaining:
        print(f"Warning: {remaining} redirect links remain", file=sys.stderr)
        return 1
    print("All redirect links replaced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
