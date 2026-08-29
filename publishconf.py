"""Production Pelican settings.

Layered over `pelicanconf.py`. The differences are the absolute site URL that
canonical links and OpenGraph tags need (spec 26), and the feeds.
"""

from __future__ import annotations

import os
import sys

sys.path.append(os.curdir)

from pelicanconf import *  # noqa: F403, E402

# Absolute URL, with no trailing slash. Canonical links, OpenGraph tags, the
# sitemap, and the feeds all build on it, so an override must not add one.
SITEURL = os.environ.get("MAWKINGBIRD_SITEURL", "https://mawkingbird.com").rstrip("/")

RELATIVE_URLS = False

FEED_ALL_ATOM = "feeds/all.atom.xml"
FEED_ALL_RSS = "feeds/all.rss.xml"
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

DELETE_OUTPUT_DIRECTORY = True

# Analytics are not required for launch and none is configured (spec 42).
