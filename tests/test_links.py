"""Sub-path link handling (the first deploy's bug, and the check that missed it).

The site is served from a GitHub project Pages sub-path. A link written
`/clients/` resolves to the origin root, loses the prefix, and 404s. The first
deploy shipped a thousand of them and reported success.

The first version of the check that was supposed to catch this passed on that
very output, because it asked "does `output/clients/elk/` exist?" -- which it
does, whether or not the link pointing at it carries the prefix. These tests
pin the distinction.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mastodon_clients.sitemap import check_local_assets, check_local_links

BASE = "https://example.github.io/project"
PREFIX = "/project"


@pytest.fixture
def site(tmp_path: Path) -> Path:
    """A built site with two pages and a stylesheet."""
    (tmp_path / "clients" / "elk").mkdir(parents=True)
    (tmp_path / "assets" / "css").mkdir(parents=True)
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    (tmp_path / "clients" / "elk" / "index.html").write_text("<html></html>", encoding="utf-8")
    (tmp_path / "assets" / "css" / "site.css").write_text("body{}", encoding="utf-8")
    return tmp_path


def _page(site: Path, html: str) -> None:
    (site / "index.html").write_text(html, encoding="utf-8")


# --- the bug that shipped --------------------------------------------------


def test_a_link_missing_the_subpath_is_broken(site: Path) -> None:
    """The exact failure of the first deploy.

    `output/clients/elk/index.html` exists, so a naive existence check passes.
    The link is still broken: served from /project/, this href resolves to
    example.github.io/clients/elk/, which is not on the site at all.
    """
    _page(site, '<a href="/clients/elk/">Elk</a>')
    assert check_local_links(site, BASE) == ["index.html -> /clients/elk/"]


def test_the_same_link_with_the_subpath_is_fine(site: Path) -> None:
    _page(site, '<a href="/project/clients/elk/">Elk</a>')
    assert check_local_links(site, BASE) == []


def test_an_absolute_url_on_our_own_host_is_fine(site: Path) -> None:
    _page(site, f'<a href="{BASE}/clients/elk/">Elk</a>')
    assert check_local_links(site, BASE) == []


def test_a_prefixed_link_to_a_missing_page_is_broken(site: Path) -> None:
    """Carrying the prefix is not sufficient; the target must exist."""
    _page(site, '<a href="/project/clients/nope/">Nope</a>')
    assert check_local_links(site, BASE) == ["index.html -> /project/clients/nope/"]


# --- what must not be flagged ----------------------------------------------


def test_external_links_are_skipped(site: Path) -> None:
    _page(
        site,
        '<a href="https://github.com/x">gh</a>'
        '<a href="//cdn.example.com/x.js">cdn</a>'
        '<a href="mailto:someone@example.com">mail</a>',
    )
    assert check_local_links(site, BASE) == []


def test_fragments_are_skipped(site: Path) -> None:
    """A fragment addresses a position on a page, not a page."""
    _page(site, '<a href="#main">skip</a>')
    assert check_local_links(site, BASE) == []


def test_a_fragment_on_a_real_page_checks_the_page(site: Path) -> None:
    _page(site, '<a href="/project/clients/elk/#features">features</a>')
    assert check_local_links(site, BASE) == []


def test_document_relative_links_are_skipped(site: Path) -> None:
    """Resolved against the containing page, which this crawl does not model."""
    _page(site, '<a href="../clients/elk/">Elk</a>')
    assert check_local_links(site, BASE) == []


def test_the_site_root_resolves(site: Path) -> None:
    _page(site, '<a href="/project/">home</a>')
    assert check_local_links(site, BASE) == []


# --- the development build, served from an origin root ---------------------


def test_an_empty_base_does_not_swallow_the_whole_web(site: Path) -> None:
    """With base="", `startswith(base)` is true of every string.

    An earlier version tested the base before testing for off-site URLs, so a
    development build classified github.com as an internal path and reported the
    entire web as broken.
    """
    _page(site, '<a href="https://github.com/x">gh</a><a href="https://mawkingbird.com/">mb</a>')
    assert check_local_links(site, "") == []


def test_root_relative_links_work_at_an_origin_root(site: Path) -> None:
    _page(site, '<a href="/clients/elk/">Elk</a>')
    assert check_local_links(site, "") == []


# --- assets ----------------------------------------------------------------


def test_a_missing_stylesheet_is_reported(site: Path) -> None:
    """A renamed asset otherwise ships as a silently unstyled site."""
    _page(site, '<link rel="stylesheet" href="/project/assets/css/gone.css">')
    assert check_local_assets(site, BASE) == ["/assets/css/gone.css"]


def test_a_present_stylesheet_is_not_reported(site: Path) -> None:
    _page(site, '<link rel="stylesheet" href="/project/assets/css/site.css">')
    assert check_local_assets(site, BASE) == []


# --- the rewriter itself ---------------------------------------------------


def test_rewriting_adds_the_prefix() -> None:
    from plugins.site_relative_links import rewrite_text

    assert rewrite_text('<a href="/clients/">c</a>', PREFIX) == '<a href="/project/clients/">c</a>'


def test_rewriting_is_idempotent() -> None:
    """Running twice must not produce /project/project/clients/."""
    from plugins.site_relative_links import rewrite_text

    once = rewrite_text('<a href="/clients/">c</a>', PREFIX)
    assert rewrite_text(once, PREFIX) == once


def test_rewriting_leaves_external_and_relative_links_alone() -> None:
    from plugins.site_relative_links import rewrite_text

    html = '<a href="https://x.test/">x</a><a href="//cdn.test/a.js">c</a><a href="../up/">u</a>'
    assert rewrite_text(html, PREFIX) == html


def test_rewriting_with_no_prefix_changes_nothing() -> None:
    """A site served from an origin root needs no rewriting."""
    from plugins.site_relative_links import rewrite_text

    html = '<a href="/clients/">c</a>'
    assert rewrite_text(html, "") == html


# --- repository collectors -------------------------------------------------
#
# Fediverse projects are unusually likely to live on a self-hosted forge. The
# collector originally matched only github.com and gitlab.com, so anything on
# Codeberg or a project's own Forgejo recorded no activity signal at all --
# which reads as `unknown` maintenance and costs 19 rating points against the
# truth. Nicolium sat at 46.6 instead of 86.0 for exactly that reason.


def test_known_self_hosted_forges_are_recognised() -> None:
    from mastodon_clients.collect import _FORGE_PATH_RE, _KNOWN_FORGES

    for url, host in (
        ("https://codeberg.org/enafore/enafore", "codeberg.org"),
        ("https://git.pleroma.social/nicolium/nicolium", "git.pleroma.social"),
    ):
        match = _FORGE_PATH_RE.match(url)
        assert match is not None
        assert match.group(1) == host
        assert host in _KNOWN_FORGES


def test_the_forge_path_pattern_splits_host_from_project() -> None:
    from mastodon_clients.collect import _FORGE_PATH_RE

    match = _FORGE_PATH_RE.match("https://git.example.org/group/subgroup/project")
    assert match is not None
    assert match.group(1) == "git.example.org"
    assert match.group(2) == "group/subgroup/project"


def test_an_unknown_host_is_probed_rather_than_abandoned() -> None:
    """Recording "host not recognised" makes a maintained project look dead."""
    from mastodon_clients.collect import _PROBE_ORDER

    assert "forgejo" in _PROBE_ORDER
    assert "gitlab" in _PROBE_ORDER
