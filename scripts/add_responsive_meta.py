#!/usr/bin/env python3
"""Add viewport meta and mobile.js to all HTML pages."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIEWPORT = '<meta name="viewport" content="width=device-width, initial-scale=1" />'
VIEWPORT_RE = re.compile(r'<meta\s+name="viewport"[^>]*>', re.IGNORECASE)
CUSTOM_CSS_RE = re.compile(
    r'(<link\s+rel="stylesheet"\s+href="[^"]*custom\.css"[^>]*/>)',
    re.IGNORECASE,
)
MOBILE_JS_MARKER = "photoria/js/mobile.js"


def mobile_script_tag(css_link: str) -> str:
    href_match = re.search(r'href="([^"]+)"', css_link, re.IGNORECASE)
    if not href_match:
        raise ValueError(f"Could not parse custom.css href from: {css_link}")
    prefix = href_match.group(1).rsplit("custom.css", 1)[0]
    return f'<script type="text/javascript" src="{prefix}js/mobile.js"></script>'


def patch_file(path: Path) -> tuple[bool, bool]:
    content = path.read_text(encoding="utf-8", errors="replace")
    changed = False
    viewport_added = False
    script_added = False

    if not VIEWPORT_RE.search(content):
        if "<head" in content.lower():
            content = re.sub(
                r"(<head[^>]*>)",
                r"\1\n" + VIEWPORT,
                content,
                count=1,
                flags=re.IGNORECASE,
            )
            changed = True
            viewport_added = True

    if MOBILE_JS_MARKER not in content:
        match = CUSTOM_CSS_RE.search(content)
        if match:
            tag = mobile_script_tag(match.group(1))
            insert_at = match.end()
            content = content[:insert_at] + "\n" + tag + content[insert_at:]
            changed = True
            script_added = True

    if changed:
        path.write_text(content, encoding="utf-8")

    return viewport_added, script_added


def main() -> int:
    viewport_count = 0
    script_count = 0
    skipped = 0

    for html in ROOT.rglob("*.html"):
        if html.parent == ROOT and re.match(r"^index[a-f0-9]+\.html$", html.name, re.I):
            continue
        vp, js = patch_file(html)
        if vp:
            viewport_count += 1
        if js:
            script_count += 1
        if not vp and not js:
            skipped += 1

    print(f"Added viewport to {viewport_count} files")
    print(f"Added mobile.js to {script_count} files")
    print(f"Skipped (already patched): {skipped} files")

    missing_viewport = 0
    missing_js = 0
    for html in ROOT.rglob("*.html"):
        if html.parent == ROOT and re.match(r"^index[a-f0-9]+\.html$", html.name, re.I):
            continue
        text = html.read_text(encoding="utf-8", errors="replace")
        if not CUSTOM_CSS_RE.search(text):
            continue
        if not VIEWPORT_RE.search(text):
            missing_viewport += 1
        if MOBILE_JS_MARKER not in text:
            missing_js += 1

    if missing_viewport or missing_js:
        print(
            f"Warning: {missing_viewport} without viewport, {missing_js} without mobile.js",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
