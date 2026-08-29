"""Shared fixtures.

Tests build a repository in a temporary directory rather than reading the real
`data/` tree, so a change to the seed data cannot break a schema test and a
schema test cannot depend on a particular client existing.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

FEATURES_TOML = """
[[feature]]
id = "multi_account"
label = "Multi-account"
description = "Several accounts at once."
core = true
page = true

[[feature]]
id = "lists"
label = "Lists"
description = "Mastodon lists as timelines."
core = true
page = false

[[feature]]
id = "keyboard_navigation"
label = "Keyboard navigation"
description = "Operable by keyboard."
core = true
page = false

[[feature]]
id = "column_layout"
label = "Column layout"
description = "Multi-column deck."
core = false
page = false

[[feature]]
id = "accessibility_features"
label = "Accessibility features"
description = "Deliberate accessibility work."
core = true
page = false
"""

AUDIENCES_TOML = """
[[audience]]
id = "power-users"
label = "Power users"
intro = "Heavy use."
criteria = ["multi_account", "lists"]

[[audience]]
id = "new-users"
label = "New users"
intro = "Just arrived."
criteria = ["accessibility_features"]
"""

CLIENT_TOML = """
schema_version = 1
slug = "{slug}"
name = "{name}"
summary = "A client for testing."
status = "active"
reviewed_at = 2026-08-29
source_model = "open-source"
license = "MIT"
deployment = "hosted-and-self-hostable"
server_dependency = "independent"
funding_model = ["donations"]
audiences = ["power-users"]

[links]
homepage = "https://{slug}.example.com/"
source = "https://github.com/example/{slug}"
issues = "https://github.com/example/{slug}/issues"

[features]
multi_account = true
lists = true
keyboard_navigation = "partial"
column_layout = false
accessibility_features = true
"""


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A minimal but complete repository: taxonomy plus two clients."""
    (tmp_path / "data" / "taxonomy").mkdir(parents=True)
    (tmp_path / "data" / "clients").mkdir(parents=True)
    (tmp_path / "content" / "generated" / "clients").mkdir(parents=True)
    (tmp_path / "content" / "overrides" / "clients").mkdir(parents=True)

    (tmp_path / "data" / "taxonomy" / "features.toml").write_text(FEATURES_TOML, encoding="utf-8")
    (tmp_path / "data" / "taxonomy" / "audiences.toml").write_text(AUDIENCES_TOML, encoding="utf-8")

    for slug, name in (("alpha", "Alpha"), ("beta", "Beta")):
        (tmp_path / "data" / "clients" / f"{slug}.toml").write_text(
            CLIENT_TOML.format(slug=slug, name=name), encoding="utf-8"
        )
    return tmp_path


@pytest.fixture
def write_client(repo: Path):
    """Write an arbitrary client TOML into the fixture repository."""

    def _write(slug: str, body: str) -> Path:
        path = repo / "data" / "clients" / f"{slug}.toml"
        path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")
        return path

    return _write


@pytest.fixture
def write_observations(repo: Path):
    """Write an observations file into the fixture repository."""

    def _write(updated_at: str, rows: list[dict[str, object]]) -> Path:
        path = repo / "data" / "generated" / "observations.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"schema_version": 1, "updated_at": updated_at, "observations": rows}, indent=2),
            encoding="utf-8",
        )
        return path

    return _write
