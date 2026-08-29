"""Prose merging (spec 20, invariant 3)."""

from __future__ import annotations

from pathlib import Path

from mastodon_clients.errors import ValidationReport
from mastodon_clients.overrides import (
    GENERATED_DIR,
    OVERRIDE_DIR,
    SECTIONS,
    load_prose,
    merge,
    parse_generated,
    render_generated,
)

GENERATED = """---
slug: alpha
model: test-model
prompt_version: 1
---

<!-- section: summary -->

Generated summary text.

<!-- section: maintenance -->

Generated maintenance text.

<!-- section: verdict -->

Generated verdict text.
"""


def _write_generated(repo: Path, slug: str, text: str = GENERATED) -> Path:
    path = repo / GENERATED_DIR / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _write_override(repo: Path, slug: str, body: str) -> Path:
    path = repo / OVERRIDE_DIR / f"{slug}.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_generated_prose_round_trips() -> None:
    sections = {"summary": "One.", "maintenance": "Two.", "verdict": "Three."}
    provenance = {"model": "test-model", "prompt_version": "1"}
    rendered = render_generated("alpha", sections, provenance)
    parsed = parse_generated(rendered, "alpha")

    assert parsed.sections == sections
    assert parsed.provenance["model"] == "test-model"


def test_rendering_is_deterministic() -> None:
    """Identical prose must produce an identical file, or every refresh diffs."""
    sections = {"verdict": "Three.", "summary": "One."}
    provenance = {"prompt_version": "1", "model": "test-model"}
    assert render_generated("alpha", sections, provenance) == render_generated("alpha", sections, provenance)


def test_sections_render_in_canonical_order() -> None:
    rendered = render_generated("alpha", {"verdict": "Last.", "summary": "First."}, {})
    assert rendered.index("section: summary") < rendered.index("section: verdict")


def test_empty_sections_are_omitted() -> None:
    rendered = render_generated("alpha", {"summary": "Text.", "verdict": "   "}, {})
    assert "section: verdict" not in rendered


# --- the merge (invariant 3) ----------------------------------------------


def test_override_replaces_only_its_own_section(repo: Path) -> None:
    _write_generated(repo, "alpha")
    _write_override(
        repo,
        "alpha",
        '[prose]\nmaintenance = "Human maintenance text."\n',
    )

    document = load_prose(repo, "alpha")
    assert document.section("maintenance") == "Human maintenance text."
    # Everything else survives untouched.
    assert document.section("summary") == "Generated summary text."
    assert document.section("verdict") == "Generated verdict text."


def test_overridden_sections_are_marked(repo: Path) -> None:
    """The page can then show which prose is the editor's own."""
    _write_generated(repo, "alpha")
    _write_override(repo, "alpha", '[prose]\nsummary = "Human summary."\n')

    document = load_prose(repo, "alpha")
    assert document.is_overridden("summary")
    assert not document.is_overridden("verdict")


def test_override_can_add_a_section_generation_omitted(repo: Path) -> None:
    _write_generated(repo, "alpha")
    _write_override(repo, "alpha", '[prose]\nfunding = "Human funding note."\n')

    document = load_prose(repo, "alpha")
    assert document.section("funding") == "Human funding note."


def test_merge_leaves_the_generated_document_unmodified() -> None:
    """The merge must not mutate its input, or a caller reusing it sees drift."""
    generated = parse_generated(GENERATED, "alpha")
    original = dict(generated.sections)
    merge(generated, {"summary": "Replaced."})
    assert generated.sections == original


def test_missing_files_are_not_errors(repo: Path) -> None:
    """A candidate record with no prose at all is a legitimate state."""
    document = load_prose(repo, "nonexistent")
    assert document.empty
    assert document.section("summary") is None


def test_override_without_generated_prose_still_renders(repo: Path) -> None:
    _write_override(repo, "alpha", '[prose]\nsummary = "Only a human wrote this."\n')
    document = load_prose(repo, "alpha")
    assert document.section("summary") == "Only a human wrote this."


# --- validation of prose files --------------------------------------------


def test_unknown_override_section_is_reported(repo: Path) -> None:
    _write_generated(repo, "alpha")
    _write_override(repo, "alpha", '[prose]\nnonsense = "Not a real section."\n')

    report = ValidationReport()
    load_prose(repo, "alpha", report)
    assert any("unknown prose section 'nonsense'" in str(issue) for issue in report.issues)


def test_unknown_top_level_override_key_is_reported(repo: Path) -> None:
    _write_generated(repo, "alpha")
    _write_override(repo, "alpha", '[metadata]\nauthor = "Someone"\n')

    report = ValidationReport()
    load_prose(repo, "alpha", report)
    assert any("unknown top-level key 'metadata'" in str(issue) for issue in report.issues)


def test_unknown_generated_section_is_reported(repo: Path) -> None:
    """A model cannot introduce a section the client template does not render."""
    _write_generated(
        repo,
        "alpha",
        "---\nslug: alpha\n---\n\n<!-- section: invented_section -->\n\nText.\n",
    )
    report = ValidationReport()
    load_prose(repo, "alpha", report)
    assert any("unknown prose section 'invented_section'" in str(issue) for issue in report.issues)


def test_every_canonical_section_has_a_label() -> None:
    """A section without a label would render as an unheaded block of prose."""
    from mastodon_clients.overrides import SECTION_LABELS

    assert set(SECTIONS) == set(SECTION_LABELS)
