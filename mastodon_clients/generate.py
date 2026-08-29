"""Per-client prose generation (spec 18).

Two invariants live here, and both are enforced by code rather than by care:

    Invariant 2 -- generating or refreshing one client review does not
    regenerate unrelated reviews.

    Invariant 3 -- human prose overrides survive all LLM regeneration.

The second is structural: this module has no code path that writes to
`content/overrides/`. The first is checked: every generated file is hashed
before the write and re-hashed after, and a mismatch anywhere but the target is
a hard failure.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from mastodon_clients.build_content import client_payload
from mastodon_clients.overrides import (
    GENERATED_DIR,
    OVERRIDE_DIR,
    SECTIONS,
    load_override,
    parse_generated,
    render_generated,
)
from mastodon_clients.repository import Site

PROMPT_DIR = Path("prompts")
BUILD_PROMPT_DIR = Path("build") / "prompts"


@dataclass(frozen=True, slots=True)
class PromptBundle:
    """Everything assembled for one generation call."""

    slug: str
    prompt_version: str
    text: str
    client_hash: str
    source_hash: str


def generate_review(site: Site, slug: str, *, refresh: bool = False, model: str = "claude-opus-5") -> int:
    """Generate prose for exactly one client.

    Returns a process exit code. When no API key is configured the assembled
    prompt is written to `build/prompts/<slug>.md` and the command stops, so
    prose can be produced elsewhere and pasted in -- the ordinary build never
    depends on either path (invariant 1).
    """
    client = site.client(slug)
    if client is None:
        known = ", ".join(c.slug for c in site.clients)
        print(f"Unknown client {slug!r}. Known slugs: {known}", file=sys.stderr)
        return 1

    # Snapshot every other generated file so the no-collateral-damage claim can
    # be checked rather than asserted (invariant 2).
    before = _hash_generated_tree(site.root, exclude=slug)
    overrides_before = _hash_override_tree(site.root)

    bundle = _assemble_prompt(site, slug, refresh=refresh)

    prompt_path = site.root / BUILD_PROMPT_DIR / f"{slug}.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(bundle.text, encoding="utf-8")

    sections = _call_model(bundle, model=model)
    if sections is None:
        print(f"No ANTHROPIC_API_KEY set. The assembled prompt is at {prompt_path}.")
        print("Produce the prose elsewhere, then write it to")
        print(f"  {GENERATED_DIR / f'{slug}.md'}")
        print("using one '<!-- section: <id> -->' marker per section.")
        return 0

    provenance = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "prompt_version": bundle.prompt_version,
        "model": model,
        "client_hash": bundle.client_hash,
        "source_hash": bundle.source_hash,
    }

    target = site.root / GENERATED_DIR / f"{slug}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_generated(slug, sections, provenance), encoding="utf-8")
    print(f"Wrote {target}.")

    # The checks that make invariants 2 and 3 real.
    after = _hash_generated_tree(site.root, exclude=slug)
    if after != before:
        changed = sorted(set(before) ^ set(after)) or sorted(k for k in before if before[k] != after.get(k))
        print(f"ERROR: generating {slug!r} altered other reviews: {changed}", file=sys.stderr)
        return 1

    if _hash_override_tree(site.root) != overrides_before:
        print(f"ERROR: generating {slug!r} altered a human override file.", file=sys.stderr)
        return 1

    return 0


# --- prompt assembly -------------------------------------------------------


def _assemble_prompt(site: Site, slug: str, *, refresh: bool) -> PromptBundle:
    """Build the full prompt from the prompt template plus this client's facts."""
    client = site.client(slug)
    assert client is not None  # checked by the caller

    template_name = "refresh-review.md" if refresh else "client-review.md"
    template_path = site.root / PROMPT_DIR / template_name
    template = template_path.read_text(encoding="utf-8")

    version = "unversioned"
    for line in template.splitlines():
        if line.lower().startswith("prompt_version:"):
            version = line.split(":", 1)[1].strip()
            break

    payload = client_payload(site, client)
    # The rating is computed by code and is not the model's business (spec 17,
    # invariant 4), so it is withheld from the prompt entirely -- a model that
    # cannot see a score cannot be tempted to justify one.
    facts = {key: value for key, value in payload.items() if key not in ("rating", "prose", "related")}
    facts_json = json.dumps(facts, indent=2, sort_keys=True, ensure_ascii=False)

    parts = [template, "\n\n---\n\n## Structured facts for this client\n\n```json\n", facts_json, "\n```\n"]

    # Source material an editor placed beside the client record, if any.
    source_path = site.root / "data" / "sources" / f"{slug}.md"
    source_text = source_path.read_text(encoding="utf-8") if source_path.is_file() else ""
    if source_text:
        parts.append("\n---\n\n## Supplied source material\n\n")
        parts.append(source_text)

    generated_path = site.root / GENERATED_DIR / f"{slug}.md"
    if refresh and generated_path.is_file():
        existing = parse_generated(generated_path.read_text(encoding="utf-8"), slug)
        parts.append("\n---\n\n## Existing generated prose (may be revised)\n\n")
        for section_id in SECTIONS:
            text = existing.section(section_id)
            if text:
                parts.append(f"### {section_id}\n\n{text}\n\n")

    # Human overrides go in as read-only context so a refresh does not contradict
    # what an editor has already said -- but the model may not rewrite them, and
    # structurally cannot: nothing here writes to the override tree (spec 35).
    override_path = site.root / OVERRIDE_DIR / f"{slug}.toml"
    if override_path.is_file():
        from mastodon_clients.errors import ValidationReport

        overrides = load_override(override_path, ValidationReport())
        if overrides:
            parts.append("\n---\n\n## Human editorial overrides (CONTEXT ONLY -- DO NOT REWRITE)\n\n")
            parts.append(
                "The following sections have been written by the editor and will replace anything you\n"
                "produce for them. Read them so your other sections do not contradict them. Do not\n"
                "reproduce, revise, or comment on them.\n\n"
            )
            for section_id, text in sorted(overrides.items()):
                parts.append(f"### {section_id}\n\n{text}\n\n")

    text = "".join(parts)
    return PromptBundle(
        slug=slug,
        prompt_version=version,
        text=text,
        client_hash=_hash_text(Path(client.source_file).read_text(encoding="utf-8")),
        source_hash=_hash_text(source_text) if source_text else "none",
    )


def _call_model(bundle: PromptBundle, model: str) -> dict[str, str] | None:
    """Call the Anthropic API, or return None when no key is configured.

    Returning None rather than raising is deliberate: an editor without a key
    should still get a usable prompt file, not an error.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic
    except ImportError:
        print(
            "ANTHROPIC_API_KEY is set but the anthropic package is not installed.\n"
            "Install it with: uv pip install anthropic",
            file=sys.stderr,
        )
        return None

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": bundle.text}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return _parse_sections(text)


def _parse_sections(text: str) -> dict[str, str]:
    """Pull `<!-- section: id -->` blocks out of a model response.

    Unrecognised section ids are dropped rather than written, so a model cannot
    invent a section the client template does not render.
    """
    document = parse_generated(text, slug="")
    return {section_id: body for section_id, body in document.sections.items() if section_id in SECTIONS}


# --- integrity checks ------------------------------------------------------


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _hash_generated_tree(root: Path, exclude: str) -> dict[str, str]:
    """Hash every generated review except the one being written."""
    directory = root / GENERATED_DIR
    if not directory.is_dir():
        return {}
    return {
        path.name: _hash_text(path.read_text(encoding="utf-8"))
        for path in sorted(directory.glob("*.md"))
        if path.stem != exclude
    }


def _hash_override_tree(root: Path) -> dict[str, str]:
    """Hash every human override file, including the target client's.

    Unlike the generated tree, nothing is excluded: no generation may touch any
    override, not even the one for the client being regenerated (invariant 3).
    """
    directory = root / OVERRIDE_DIR
    if not directory.is_dir():
        return {}
    return {path.name: _hash_text(path.read_text(encoding="utf-8")) for path in sorted(directory.glob("*.toml"))}
