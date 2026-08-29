"""Pelican configuration for local development.

Pelican's job here is narrow: turn the content `mastodon_clients.build_content`
prepared into HTML (spec 46). It performs no data processing of its own, and the
build reaches no third-party site (invariant 1).

`publishconf.py` layers production settings over this file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

AUTHOR = "Matthew Martin"
SITENAME = "Mastodon Web Clients"
SITESUBTITLE = "A directory and review site for Mastodon-compatible web clients"
SITEURL = ""

PATH = "content"
TIMEZONE = "UTC"
DEFAULT_LANG = "en"
LOCALE = "C"

# Prose links are written site-root-relative (`/clients/`), which breaks when
# the site is served from a project Pages sub-path. The plugin rewrites them at
# render time; `check_local_links` fails the build if any slip past it.
PLUGIN_PATHS = ["plugins"]
PLUGINS = ["site_relative_links"]

THEME = "theme/mastodon_clients"
# The theme's static tree is copied to /assets/ rather than Pelican's default
# /theme/, which reads as an implementation detail in a URL.
THEME_STATIC_DIR = "assets"

# Content layout. `_generated/` is rewritten on every build by build-content;
# `pages/` is hand-written and never touched by the generator.
ARTICLE_PATHS: list[str] = []
PAGE_PATHS = ["pages", "_generated"]
# The JSON under `content/extra/` holds the machine-readable feeds of spec 27,
# copied verbatim so the JSON and the HTML necessarily derive from one source.
# CSS and JS live in the theme's own static tree, which Pelican copies itself.
STATIC_PATHS = ["extra"]

# Spec 27 names `/clients.json`, `/clients/<slug>.json`, and `/features.json`,
# so the copied files are relocated out of /extra/ onto those URLs. Per-client
# JSON at `/clients/<slug>.json` sits alongside, not inside, the HTML page at
# `/clients/<slug>/`, so the two never collide.
#
# The per-client entries are filled in by `_extra_client_json()` below rather
# than listed by hand, since the set changes whenever a client is added.
EXTRA_PATH_METADATA: dict[str, dict[str, str]] = {
    "extra/clients.json": {"path": "clients.json"},
    "extra/features.json": {"path": "features.json"},
}


def _extra_client_json() -> None:
    """Map each `content/extra/clients/<slug>.json` onto `/clients/<slug>.json`."""
    directory = Path(PATH) / "extra" / "clients"
    if not directory.is_dir():
        return
    for path in sorted(directory.glob("*.json")):
        EXTRA_PATH_METADATA[f"extra/clients/{path.name}"] = {"path": f"clients/{path.name}"}


_extra_client_json()

# Every generated page sets its own URL and Save_as, so these defaults only
# apply to hand-written pages in `content/pages/`.
PAGE_URL = "{slug}/"
PAGE_SAVE_AS = "{slug}/index.html"
INDEX_SAVE_AS = ""
ARCHIVES_SAVE_AS = ""
AUTHORS_SAVE_AS = ""
CATEGORIES_SAVE_AS = ""
TAGS_SAVE_AS = ""
CATEGORY_SAVE_AS = ""
TAG_SAVE_AS = ""
AUTHOR_SAVE_AS = ""

# No feeds during development; publishconf.py turns the real ones on.
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

DEFAULT_PAGINATION = False
RELATIVE_URLS = True
DELETE_OUTPUT_DIRECTORY = True
CACHE_CONTENT = False
LOAD_CONTENT_CACHE = False

MARKDOWN: dict[str, Any] = {
    "extension_configs": {
        "markdown.extensions.extra": {},
        "markdown.extensions.meta": {},
        "markdown.extensions.smarty": {},
    },
    "output_format": "html5",
}

# Contact routes shown on the About and submission pages (spec 5.9).
GITHUB_REPO = "https://github.com/matthewdeanmartin/mastodon_clients"
MASTODON_CONTACT = "@mistersql@mastodon.social"
MASTODON_CONTACT_URL = "https://mastodon.social/@mistersql"


def _load_data(value: str | None) -> Any:
    """Parse the JSON payload `build_content` put in a page's `Data` metadata.

    Templates call this filter and then render; the join already happened in
    Python (spec 46).
    """
    if not value:
        return {}
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}


def _markdown(text: str | None) -> str:
    """Render a prose section's Markdown to HTML.

    Prose sections are stored as Markdown so a human override reads naturally in
    its TOML file. Rendering happens here rather than in `build_content` so the
    stored prose stays diffable as text.
    """
    if not text:
        return ""
    import markdown as _markdown_lib

    return _markdown_lib.markdown(text, extensions=["extra", "smarty"])


JINJA_FILTERS = {"data": _load_data, "md": _markdown}

JINJA_ENVIRONMENT = {
    "trim_blocks": True,
    "lstrip_blocks": True,
}

# The directory table, feature pages, and facets are all rendered from templates
# that need these; exposing them once keeps templates free of imports.
DIRECTORY_SORT_DEFAULT = "name"
