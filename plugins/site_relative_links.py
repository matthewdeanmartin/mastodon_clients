"""Rewrite site-root-relative links to sit under the site's base path.

The site is served from a GitHub *project* Pages URL, so it lives under a
sub-path (`/mastodon_clients/`) rather than at an origin root. A link written
`/clients/` therefore resolves to the origin root, drops the prefix, and 404s.
The first deploy shipped twenty-two such links from Markdown prose, and a second
set from Jinja macros -- macros do not inherit the calling template's context, so
a hand-written `{{ SITEURL }}` inside one silently renders as nothing.

Both classes have the same fix, so rather than asking every author and every
template to remember a prefix, links are written site-root-relative everywhere
and get the prefix added here, once, at the end.

This runs on the *finished output* rather than on Pelican's content objects.
That is deliberate: most pages here carry no Markdown body at all -- their data
rides in metadata and is rendered entirely by templates -- so a
`content_object_init` handler sees an empty body and misses exactly the links
that matter. The rendered file is the only place every link exists.

`check_local_links` in `sitemap.py` then fails the build if anything slips past.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# `href` or `src` whose value begins with a single slash: site-root-relative.
# A protocol-relative URL (`//example.com`) points at another host, so the second
# character must not be a slash.
_ROOT_RELATIVE = re.compile(r'(?P<attr>href|src)="(?P<path>/(?!/)[^"]*)"')


def rewrite_text(text: str, prefix: str) -> str:
    """Prefix every site-root-relative link in one document.

    Idempotent: a link already carrying the prefix is left alone, so running
    twice cannot produce `/mastodon_clients/mastodon_clients/`.
    """
    if not prefix:
        return text

    def replace(match: re.Match[str]) -> str:
        path = match.group("path")
        if path == prefix or path.startswith(f"{prefix}/"):
            return match.group(0)
        return f'{match.group("attr")}="{prefix}{path}"'

    return _ROOT_RELATIVE.sub(replace, text)


def rewrite_output(output: Path, site_url: str) -> int:
    """Rewrite every HTML file under `output`. Returns the number changed."""
    prefix = urlparse(site_url.rstrip("/")).path.rstrip("/")
    if not prefix:
        # Served from an origin root, as in a development build. Nothing to do.
        return 0

    changed = 0
    for page in sorted(output.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        rewritten = rewrite_text(text, prefix)
        if rewritten != text:
            page.write_text(rewritten, encoding="utf-8")
            changed += 1
    return changed


def _finalized(pelican: Any) -> None:
    """Pelican hook: run once the whole site has been written to disk."""
    rewrite_output(Path(pelican.settings["OUTPUT_PATH"]), pelican.settings.get("SITEURL", ""))


def register() -> None:
    from pelican import signals

    signals.finalized.connect(_finalized)
