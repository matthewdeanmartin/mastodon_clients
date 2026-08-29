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
_HREF = re.compile(r'href="([^"]*)"')

# Returned for a link that resolves outside the deployed site -- a root-relative
# href missing the project sub-path. No file can satisfy it, so it is always
# broken, however real the file it was aiming at may be.
_OUTSIDE_SITE = "<outside-site>"

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


def check_local_links(output: Path, site_url: str) -> list[str]:
    """Verify every internal link resolves, as a browser would resolve it.

    The first deploy shipped links written `/clients/` in prose and in Jinja
    macros. Served from a project Pages sub-path they resolve to the origin root,
    losing the prefix, and every one 404s -- on a build reporting success.

    The subtle part, and the reason an earlier version of this check passed on
    that very output: it is not enough to ask whether `output/clients/elk/`
    exists. It does, whether or not the link pointing at it carries the prefix.
    The question is what the *href* resolves to against the deployed base URL,
    so that is what is computed here.

    Returns the broken references, each as "page -> target".
    """
    base = site_url.rstrip("/")
    prefix = urlparse(base).path.rstrip("/")

    broken: set[str] = set()
    for page in sorted(output.rglob("*.html")):
        source = page.relative_to(output).as_posix()
        for reference in _HREF.findall(page.read_text(encoding="utf-8")):
            target = _internal_target(reference, base, prefix)
            if target is not None and not _resolves(output, target):
                broken.add(f"{source} -> {reference}")
    return sorted(broken)


def _internal_target(reference: str, base: str, prefix: str) -> str | None:
    """Resolve an href to a path under the site root, or None if not ours.

    Resolution mirrors a browser's: an absolute URL on our host keeps whatever
    follows the base; a root-relative href is resolved against the *origin*, not
    the base, which is precisely why one missing prefix breaks a link.
    """
    reference = reference.split("#", 1)[0]
    if not reference:
        return None

    # Off-site first. Order matters: with an empty base -- a development build
    # served from a directory root -- `startswith(base)` is true of every string,
    # so testing the base first would classify the whole web as internal.
    if reference.startswith("//") or "://" in reference or reference.startswith("mailto:"):
        return None

    if base and reference.startswith(base):
        return reference[len(base) :] or "/"

    if reference.startswith("/"):
        # A browser resolves this against the origin root. Under a sub-path the
        # link only reaches the site if it already carries the prefix; without
        # one it lands outside the site, which is a broken link even though the
        # file it was aiming at exists.
        if prefix:
            if reference == prefix or reference.startswith(f"{prefix}/"):
                return reference[len(prefix) :] or "/"
            return _OUTSIDE_SITE
        return reference

    # Document-relative; resolved against the containing page, which this crawl
    # does not model. Left alone rather than guessed at.
    return None


def _resolves(output: Path, target: str) -> bool:
    """Whether a site-relative path was actually written."""
    if target is _OUTSIDE_SITE:
        # Resolved outside the deployed site: no file can satisfy it.
        return False
    relative = target.lstrip("/")
    if not relative:
        return (output / "index.html").is_file()
    candidate = output / relative
    # A directory URL is served by its index.html.
    return candidate.is_file() or (candidate / "index.html").is_file()


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
