"""Merging of LLM-generated prose with human overrides (spec 20).

Invariant 3 -- human prose overrides survive all LLM regeneration -- is enforced
structurally rather than by convention: generated prose and overrides live in
separate file trees, and nothing in this module or in the generator ever writes
to the override tree.

The merge is section-granular. An editor who rewrites only the maintenance
paragraph keeps the regenerated text for every other section.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from mastodon_clients.errors import ValidationReport

# The canonical prose sections. A generated file may omit sections; it may not
# invent new ones, because the client template renders these by name.
SECTIONS: tuple[str, ...] = (
    "summary",
    "who_is_it_for",
    "notable_features",
    "deployment",
    "source_and_licensing",
    "funding",
    "maintenance",
    "support",
    "verdict",
)

SECTION_LABELS: dict[str, str] = {
    "summary": "Summary",
    "who_is_it_for": "Who it is for",
    "notable_features": "Notable features",
    "deployment": "Deployment",
    "source_and_licensing": "Source and licensing",
    "funding": "Funding",
    "maintenance": "Maintenance",
    "support": "Support",
    "verdict": "In short",
}

# Sections are delimited by an HTML comment so the file stays readable as
# Markdown while remaining unambiguous to parse. A heading would be ambiguous:
# generated prose contains headings of its own.
_SECTION_RE = re.compile(r"^<!--\s*section:\s*([a-z_]+)\s*-->\s*$", re.MULTILINE)

GENERATED_DIR = Path("content") / "generated" / "clients"
OVERRIDE_DIR = Path("content") / "overrides" / "clients"


@dataclass(frozen=True, slots=True)
class ProseDocument:
    """Prose for one client, by section id, plus its provenance front matter."""

    slug: str
    sections: dict[str, str]
    provenance: dict[str, str]
    # Section ids whose text came from the override file rather than generation.
    overridden: frozenset[str] = frozenset()

    def section(self, section_id: str) -> str | None:
        text = self.sections.get(section_id)
        return text if text and text.strip() else None

    def is_overridden(self, section_id: str) -> bool:
        return section_id in self.overridden

    @property
    def empty(self) -> bool:
        return not any(self.section(section_id) for section_id in SECTIONS)


def render_generated(slug: str, sections: dict[str, str], provenance: dict[str, str]) -> str:
    """Serialise a generated prose file.

    Deterministic: sections are emitted in canonical order and provenance keys
    are sorted, so regenerating identical prose produces an identical file and
    shows no diff.
    """
    lines = ["---"]
    lines.append(f"slug: {slug}")
    for key in sorted(provenance):
        lines.append(f"{key}: {provenance[key]}")
    lines.append("---")
    lines.append("")
    for section_id in SECTIONS:
        text = sections.get(section_id)
        if not text or not text.strip():
            continue
        lines.append(f"<!-- section: {section_id} -->")
        lines.append("")
        lines.append(text.strip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_generated(text: str, slug: str) -> ProseDocument:
    """Parse a generated prose file back into sections and provenance."""
    provenance: dict[str, str] = {}
    body = text

    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    provenance[key.strip()] = value.strip()
            body = text[end + 4 :]

    sections: dict[str, str] = {}
    matches = list(_SECTION_RE.finditer(body))
    for index, match in enumerate(matches):
        section_id = match.group(1)
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[section_id] = body[start:end].strip()

    provenance.pop("slug", None)
    return ProseDocument(slug=slug, sections=sections, provenance=provenance)


def load_prose(root: Path, slug: str, report: ValidationReport | None = None) -> ProseDocument:
    """Load generated prose for a client and merge any human overrides over it.

    Both files are optional. A client with neither renders with structured facts
    only, which is a legitimate state for a `candidate` record.
    """
    report = report if report is not None else ValidationReport()

    generated_path = root / GENERATED_DIR / f"{slug}.md"
    if generated_path.is_file():
        document = parse_generated(generated_path.read_text(encoding="utf-8"), slug)
        for section_id in document.sections:
            if section_id not in SECTIONS:
                report.add(str(generated_path), f"unknown prose section {section_id!r}")
    else:
        document = ProseDocument(slug=slug, sections={}, provenance={})

    override_path = root / OVERRIDE_DIR / f"{slug}.toml"
    if not override_path.is_file():
        return document

    return merge(document, load_override(override_path, report))


def load_override(path: Path, report: ValidationReport) -> dict[str, str]:
    """Read a human override file's `[prose]` table."""
    try:
        with path.open("rb") as handle:
            raw = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        report.add(str(path), f"invalid TOML: {exc}")
        return {}

    for key in raw:
        if key != "prose":
            report.add(str(path), f"unknown top-level key {key!r}; overrides carry only [prose]")

    prose = raw.get("prose", {})
    if not isinstance(prose, dict):
        report.add(str(path), "[prose] must be a table")
        return {}

    sections: dict[str, str] = {}
    for section_id, value in prose.items():
        if section_id not in SECTIONS:
            report.add(str(path), f"unknown prose section {section_id!r}")
            continue
        if not isinstance(value, str):
            report.add(str(path), f"[prose].{section_id} must be a string")
            continue
        if value.strip():
            sections[section_id] = value.strip()
    return sections


def merge(generated: ProseDocument, overrides: dict[str, str]) -> ProseDocument:
    """Replace matching sections only; leave everything else untouched.

    This is the whole of invariant 3's build-time half. The other half is that
    no generation command writes to the override tree at all.
    """
    merged = dict(generated.sections)
    merged.update(overrides)
    return ProseDocument(
        slug=generated.slug,
        sections=merged,
        provenance=generated.provenance,
        overridden=frozenset(overrides),
    )
