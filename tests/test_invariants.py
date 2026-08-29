"""The architectural invariants of spec 52, as executable checks.

Spec 43 names two of these explicitly as things the suite must verify:

    regenerating one client does not alter another client's generated content

    regenerating an LLM review does not alter human prose overrides

Both are here, along with the offline-build and no-JavaScript-required
invariants that are equally structural.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mastodon_clients.build_content import build_content
from mastodon_clients.generate import _hash_generated_tree, _hash_override_tree, generate_review
from mastodon_clients.overrides import GENERATED_DIR, OVERRIDE_DIR, load_prose, render_generated
from mastodon_clients.repository import load_site


def _seed_prose(repo: Path, slug: str, text: str) -> Path:
    path = repo / GENERATED_DIR / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_generated(slug, {"summary": text}, {"model": "seed"}), encoding="utf-8")
    return path


def _seed_override(repo: Path, slug: str, text: str) -> Path:
    path = repo / OVERRIDE_DIR / f"{slug}.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'[prose]\nsummary = """\n{text}\n"""\n', encoding="utf-8")
    return path


def _prompts(repo: Path) -> None:
    """Minimal prompt files, so generation can assemble without the real ones."""
    directory = repo / "prompts"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "client-review.md").write_text("prompt_version: test\n\nWrite prose.\n", encoding="utf-8")
    (directory / "refresh-review.md").write_text("prompt_version: test\n\nRevise prose.\n", encoding="utf-8")


@pytest.fixture
def stub_model(monkeypatch: pytest.MonkeyPatch):
    """Stand in for the API call, so generation can be tested without a network.

    That this is possible at all is itself the point: the generator's contract
    is "produce sections", and everything around it is checkable offline.
    """

    def _install(sections: dict[str, str]) -> None:
        monkeypatch.setattr("mastodon_clients.generate._call_model", lambda bundle, model: sections)

    return _install


# --- Invariant 2: one client at a time ------------------------------------


def test_generating_one_review_leaves_other_reviews_byte_identical(
    repo: Path, stub_model, capsys: pytest.CaptureFixture[str]
) -> None:
    """Spec 43's first named invariant."""
    _prompts(repo)
    _seed_prose(repo, "alpha", "Alpha's original summary.")
    beta_path = _seed_prose(repo, "beta", "Beta's original summary.")
    beta_before = beta_path.read_bytes()

    stub_model({"summary": "Alpha's regenerated summary."})
    site = load_site(repo)
    assert generate_review(site, "alpha") == 0

    assert beta_path.read_bytes() == beta_before
    alpha = (repo / GENERATED_DIR / "alpha.md").read_text(encoding="utf-8")
    assert "regenerated" in alpha


def test_generation_reports_collateral_damage(repo: Path, stub_model, monkeypatch: pytest.MonkeyPatch) -> None:
    """The guard is real: if something did touch a neighbour, the run fails.

    Simulated by having the stubbed model write to another client's file as a
    side effect -- exactly the failure mode invariant 2 exists to catch.
    """
    _prompts(repo)
    _seed_prose(repo, "alpha", "Alpha's summary.")
    beta_path = _seed_prose(repo, "beta", "Beta's summary.")

    def _saboteur(bundle: Any, model: str) -> dict[str, str]:
        beta_path.write_text("clobbered", encoding="utf-8")
        return {"summary": "Alpha's regenerated summary."}

    monkeypatch.setattr("mastodon_clients.generate._call_model", _saboteur)
    site = load_site(repo)
    assert generate_review(site, "alpha") == 1


def test_generation_refuses_an_unknown_client(repo: Path, stub_model) -> None:
    _prompts(repo)
    stub_model({"summary": "Text."})
    site = load_site(repo)
    assert generate_review(site, "nonexistent") == 1


# --- Invariant 3: overrides survive regeneration --------------------------


def test_regeneration_leaves_human_overrides_byte_identical(repo: Path, stub_model) -> None:
    """Spec 43's second named invariant."""
    _prompts(repo)
    _seed_prose(repo, "alpha", "Generated summary.")
    override_path = _seed_override(repo, "alpha", "The editor's own summary.")
    override_before = override_path.read_bytes()

    stub_model({"summary": "A completely different generated summary."})
    site = load_site(repo)
    assert generate_review(site, "alpha") == 0

    assert override_path.read_bytes() == override_before


def test_the_override_still_wins_after_regeneration(repo: Path, stub_model) -> None:
    """Surviving on disk is not enough -- it must still be what renders."""
    _prompts(repo)
    _seed_prose(repo, "alpha", "Generated summary.")
    _seed_override(repo, "alpha", "The editor's own summary.")

    stub_model({"summary": "A completely different generated summary."})
    site = load_site(repo)
    generate_review(site, "alpha")

    document = load_prose(repo, "alpha")
    assert document.section("summary") == "The editor's own summary."
    assert document.is_overridden("summary")


def test_the_hash_helpers_see_what_they_claim_to(repo: Path) -> None:
    """The guard is only as good as what it watches."""
    _seed_prose(repo, "alpha", "One.")
    _seed_prose(repo, "beta", "Two.")
    _seed_override(repo, "alpha", "Editor text.")

    generated = _hash_generated_tree(repo, exclude="alpha")
    assert set(generated) == {"beta.md"}

    # Overrides exclude nothing -- not even the client being regenerated.
    overrides = _hash_override_tree(repo)
    assert set(overrides) == {"alpha.toml"}


# --- Invariant 1: an ordinary build is offline ----------------------------


def test_the_build_path_never_imports_the_collector() -> None:
    """The collector is the only networked module; the build must not reach it.

    Checked by import graph rather than by mocking sockets: a module that is
    never imported cannot make a request no matter what it contains.
    """
    import ast

    build_path_modules = [
        "mastodon_clients/repository.py",
        "mastodon_clients/build_content.py",
        "mastodon_clients/schema.py",
        "mastodon_clients/scoring.py",
        "mastodon_clients/health.py",
        "mastodon_clients/overrides.py",
        "mastodon_clients/taxonomy.py",
        "mastodon_clients/sitemap.py",
    ]
    forbidden = {"httpx", "requests", "urllib.request", "socket", "ssl", "anthropic", "mastodon_clients.collect"}

    for module in build_path_modules:
        tree = ast.parse(Path(module).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                assert name not in forbidden, f"{module} imports {name}, which is not allowed on the build path"


def test_a_build_with_no_observations_still_succeeds(repo: Path) -> None:
    """No refresh has ever run: every client reads unknown, nothing fails."""
    site = load_site(repo)
    assert site.report.ok, site.report.render()
    assert build_content(site) > 0


# --- Invariant 6: the directory works without JavaScript ------------------


def test_every_client_appears_in_the_generated_directory(repo: Path) -> None:
    """Server-rendered completeness, before any script runs."""
    site = load_site(repo)
    build_content(site)

    directory = (repo / "content" / "_generated" / "clients-index.md").read_text(encoding="utf-8")
    payload = json.loads(directory.split("Data: ", 1)[1])
    listed = {client["slug"] for client in payload["clients"]}
    assert listed == {c.slug for c in site.listed}


def test_every_client_gets_its_own_page(repo: Path) -> None:
    site = load_site(repo)
    build_content(site)
    for client in site.listed:
        assert (repo / "content" / "_generated" / "clients" / f"{client.slug}.md").is_file()


# --- Invariant 4 / spec 27: one source of facts ---------------------------


def test_json_and_html_payloads_come_from_one_source(repo: Path) -> None:
    """The JSON endpoint and the page must not be able to disagree."""
    site = load_site(repo)
    build_content(site)

    from_json = json.loads((repo / "content" / "extra" / "clients" / "alpha.json").read_text(encoding="utf-8"))
    page = (repo / "content" / "_generated" / "clients" / "alpha.md").read_text(encoding="utf-8")
    from_page = json.loads(page.split("Data: ", 1)[1])

    assert from_json == from_page


# --- Determinism (spec 44) ------------------------------------------------


def test_two_builds_of_one_commit_produce_identical_output(repo: Path) -> None:
    site = load_site(repo)
    build_content(site)
    first = {
        path.relative_to(repo).as_posix(): path.read_bytes()
        for path in sorted((repo / "content").rglob("*"))
        if path.is_file()
    }

    build_content(load_site(repo))
    second = {
        path.relative_to(repo).as_posix(): path.read_bytes()
        for path in sorted((repo / "content").rglob("*"))
        if path.is_file()
    }

    assert first == second


# --- Invariant 9: dead clients keep their URL -----------------------------


def test_a_discontinued_client_keeps_its_page_and_url(repo: Path, write_client) -> None:
    write_client(
        "gone",
        """
        schema_version = 1
        slug = "gone"
        name = "Gone"
        summary = "A client that has ended."
        status = "discontinued"
        reviewed_at = 2026-08-29
        discontinued_at = 2026-03-01
        discontinued_evidence = "The maintainer announced it on the project homepage."
        source_model = "closed-source"
        deployment = "hosted"
        homepage = "https://gone.example.com/"
        successors = ["alpha"]
        """,
    )
    site = load_site(repo)
    assert site.report.ok, site.report.render()

    gone = site.client("gone")
    assert gone is not None
    assert gone.url == "/clients/gone/"
    assert gone in site.listed
    assert gone in site.historical
    assert gone not in site.published

    build_content(site)
    page = (repo / "content" / "_generated" / "clients" / "gone.md").read_text(encoding="utf-8")
    assert "Template: historical" in page


def test_candidate_and_excluded_records_are_not_published(repo: Path, write_client) -> None:
    """A record can exist without being published (spec 33)."""
    for slug, status in (("draft", "candidate"), ("outofscope", "excluded")):
        write_client(
            slug,
            f"""
            schema_version = 1
            slug = "{slug}"
            name = "{slug.title()}"
            summary = "Recorded but not published."
            status = "{status}"
            reviewed_at = 2026-08-29
            source_model = "closed-source"
            deployment = "hosted"
            homepage = "https://{slug}.example.com/"
            """,
        )
    site = load_site(repo)
    assert site.report.ok, site.report.render()

    listed = {c.slug for c in site.listed}
    assert "draft" not in listed
    assert "outofscope" not in listed
    # But the records themselves are still loaded, so the decision is recorded.
    assert site.client("outofscope") is not None
