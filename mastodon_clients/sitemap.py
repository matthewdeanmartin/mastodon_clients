"""Sitemap and robots.txt generation (spec 26).

Written after Pelican has produced `output/`, by walking the rendered HTML
rather than by re-deriving the page list. Walking the output means the sitemap
cannot disagree with what was actually published -- a list rebuilt from the data
layer could name a page a template failed to emit.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse
from xml.sax.saxutils import escape

# Rough crawl priorities. These are a hint at best; the ordering reflects how
# much of the site's value sits on each kind of page.
_PRIORITIES: tuple[tuple[str, str], ...] = (
    ("clients/", "0.9"),
    ("for/", "0.8"),
    ("features/", "0.7"),
    ("compare/", "0.5"),
    ("methodology", "0.6"),
    ("about", "0.6"),
    ("submit", "0.5"),
)


def _priority(url_path: str) -> str:
    if url_path == "":
        return "1.0"
    for prefix, value in _PRIORITIES:
        if url_path.startswith(prefix):
            return value
    return "0.6"


def _urls(output: Path) -> list[str]:
    """Every published page's site-relative URL path, sorted.

    Sorting keeps the file stable across builds, so a rebuild of an unchanged
    commit produces no diff (spec 44).
    """
    paths: set[str] = set()
    for path in output.rglob("index.html"):
        relative = path.parent.relative_to(output).as_posix()
        paths.add("" if relative == "." else f"{relative}/")
    return sorted(paths)


def write_sitemap(output: Path, site_url: str) -> int:
    """Write `sitemap.xml`. Returns the URL count."""
    base = site_url.rstrip("/")
    urls = _urls(output)

    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url_path in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(f'{base}/{url_path}')}</loc>")
        lines.append(f"    <priority>{_priority(url_path)}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")

    (output / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(urls)


def check_local_assets(output: Path, site_url: str) -> list[str]:
    """Verify every same-site asset a page references was actually written.

    A renamed stylesheet that no template followed still produces a "successful"
    build -- one that ships an unstyled site. Comparing the referenced paths
    against what is on disk turns that into a build failure instead.

    Returns the missing paths, site-relative.
    """
    base = site_url.rstrip("/")
    prefix = urlparse(base).path.rstrip("/")
    pattern = re.compile(r'(?:href|src)="([^"]+\.(?:css|js))"')

    missing: set[str] = set()
    for page in output.rglob("*.html"):
        for reference in pattern.findall(page.read_text(encoding="utf-8")):
            if reference.startswith(base):
                relative = reference[len(base) :]
            elif reference.startswith("/"):
                # Root-relative: strip the project sub-path if it carries one.
                relative = reference[len(prefix) :] if prefix and reference.startswith(prefix) else reference
            else:
                # Off-site or genuinely relative; not ours to verify.
                continue
            if not (output / relative.lstrip("/")).is_file():
                missing.add(relative)
    return sorted(missing)


def write_robots(output: Path, site_url: str) -> None:
    """Write `robots.txt`.

    Nothing is disallowed. Arbitrary filter combinations never become URLs in
    the first place -- the directory keeps that state in the fragment (spec 30)
    -- so there is no low-value crawl space to fence off.
    """
    base = site_url.rstrip("/")
    content = f"""User-agent: *
Allow: /

Sitemap: {base}/sitemap.xml
"""
    (output / "robots.txt").write_text(content, encoding="utf-8")
