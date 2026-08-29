"""Mawkingbird: a static directory of Mastodon-compatible web clients.

The package is the data layer. Pelican renders; this code validates, normalises,
scores, joins, and decides what pages exist (spec 46).

Nothing here performs network I/O during an ordinary build. Collection lives in
`mawkingbird.collect`, which is invoked explicitly and never imported by the
build path (invariant 1).
"""

from __future__ import annotations

__version__ = "0.1.0"
SITE_URL = "https://mawkingbird.com"
