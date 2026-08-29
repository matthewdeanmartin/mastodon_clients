"""Parsing and validation of `data/clients/*.toml`.

Two rules shape this module.

First, unknown keys are errors (spec 8). A typo'd key that silently disappears
is worse than a build failure, because the fact it was meant to record then
exists nowhere -- not in the HTML, not in the JSON, not in the score.

Second, validation accumulates (spec 24). `load_clients` returns whatever
parsed plus a report of everything wrong, so one broken record does not hide the
other nineteen.
"""

from __future__ import annotations

import re
import tomllib
from datetime import date
from enum import StrEnum
from pathlib import Path
from urllib.parse import urlparse

from mastodon_clients.errors import ValidationReport
from mastodon_clients.models import (
    LINK_TYPES,
    Client,
    Deployment,
    FeatureValue,
    Funding,
    Lifecycle,
    Link,
    Prose,
    Screenshot,
    ServerDependency,
    SourceModel,
)
from mastodon_clients.taxonomy import Taxonomy

SCHEMA_VERSION = 1

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Top-level keys of a client document. Anything else is an error.
_TOP_REQUIRED = {
    "schema_version",
    "slug",
    "name",
    "summary",
    "status",
    "source_model",
    "deployment",
    "reviewed_at",
}
_TOP_OPTIONAL = {
    "license",
    "server_dependency",
    "funding_model",
    "audiences",
    "homepage",
    "links",
    "features",
    "screenshots",
    "review",
    "discontinued_at",
    "discontinued_evidence",
    "successors",
}


def load_clients(root: Path, taxonomy: Taxonomy, report: ValidationReport) -> tuple[Client, ...]:
    """Load and validate every client record under `data/clients/`.

    Records are returned sorted by slug so downstream output is deterministic
    regardless of filesystem ordering (spec 44).
    """
    directory = root / "data" / "clients"
    if not directory.is_dir():
        report.add(str(directory), "missing client data directory")
        return ()

    clients: list[Client] = []
    seen_slugs: dict[str, str] = {}

    for path in sorted(directory.glob("*.toml")):
        client = _load_client(path, taxonomy, report)
        if client is None:
            continue
        # Duplicate slugs would collide on one canonical URL (spec 24).
        if client.slug in seen_slugs:
            report.add(str(path), f"duplicate slug {client.slug!r}, already defined in {seen_slugs[client.slug]}")
            continue
        # A filename that disagrees with its slug makes `make generate-review
        # CLIENT=x` ambiguous, so require they match.
        if path.stem != client.slug:
            report.add(str(path), f"filename does not match slug {client.slug!r}")
            continue
        seen_slugs[client.slug] = str(path)
        clients.append(client)

    if not clients and not report.issues:
        report.add(str(directory), "no client records found")

    _validate_cross_references(clients, taxonomy, report)
    return tuple(sorted(clients, key=lambda item: item.slug))


def _load_client(path: Path, taxonomy: Taxonomy, report: ValidationReport) -> Client | None:
    where = str(path)
    try:
        with path.open("rb") as handle:
            raw = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        report.add(where, f"invalid TOML: {exc}")
        return None

    _check_keys(raw, required=_TOP_REQUIRED, optional=_TOP_OPTIONAL, where=where, report=report)

    version = raw.get("schema_version")
    if version != SCHEMA_VERSION:
        report.add(where, f"schema_version must be {SCHEMA_VERSION}, got {version!r}")

    slug = _str(raw.get("slug"), "slug", where, report)
    if slug is None:
        return None
    if not SLUG_RE.match(slug):
        report.add(where, f"slug {slug!r} must be lowercase alphanumeric words joined by single hyphens")
        return None

    name = _str(raw.get("name"), "name", where, report) or slug
    summary = _str(raw.get("summary"), "summary", where, report) or ""

    lifecycle = _enum(raw.get("status"), Lifecycle, "status", where, report) or Lifecycle.CANDIDATE
    source_model = _enum(raw.get("source_model"), SourceModel, "source_model", where, report) or SourceModel.UNKNOWN
    deployment = _enum(raw.get("deployment"), Deployment, "deployment", where, report) or Deployment.UNKNOWN
    server_dependency = (
        _enum(raw.get("server_dependency"), ServerDependency, "server_dependency", where, report)
        if "server_dependency" in raw
        else ServerDependency.UNKNOWN
    ) or ServerDependency.UNKNOWN

    reviewed_at = _date(raw.get("reviewed_at"), "reviewed_at", where, report) or date(1970, 1, 1)
    discontinued_at = _date(raw.get("discontinued_at"), "discontinued_at", where, report) if "discontinued_at" in raw else None

    licence = _str(raw.get("license"), "license", where, report) if "license" in raw else None

    funding = _enum_list(raw.get("funding_model", []), Funding, "funding_model", where, report)
    audiences = _str_list(raw.get("audiences", []), "audiences", where, report)
    for audience_id in audiences:
        if audience_id not in taxonomy.audience_ids:
            report.add(where, f"audiences references unknown audience {audience_id!r}")

    features = _parse_features(raw.get("features", {}), taxonomy, where, report)
    links = _parse_links(raw, where, report)
    screenshots = _parse_screenshots(raw.get("screenshots", []), where, report)
    prose = _parse_prose(raw.get("review", {}), where, report)

    successors = _str_list(raw.get("successors", []), "successors", where, report)
    discontinued_evidence = (
        _str(raw.get("discontinued_evidence"), "discontinued_evidence", where, report)
        if "discontinued_evidence" in raw
        else None
    )

    _validate_combinations(
        where=where,
        report=report,
        lifecycle=lifecycle,
        source_model=source_model,
        licence=licence,
        links=links,
        discontinued_at=discontinued_at,
        discontinued_evidence=discontinued_evidence,
    )

    return Client(
        slug=slug,
        name=name,
        summary=summary,
        lifecycle=lifecycle,
        source_model=source_model,
        deployment=deployment,
        server_dependency=server_dependency,
        reviewed_at=reviewed_at,
        licence=licence,
        funding_model=funding,
        audiences=audiences,
        features=features,
        links=links,
        screenshots=screenshots,
        prose=prose,
        discontinued_at=discontinued_at,
        discontinued_evidence=discontinued_evidence,
        successors=successors,
        source_file=str(path),
    )


# --- field parsers ---------------------------------------------------------


def _check_keys(
    table: dict[str, object],
    *,
    required: set[str],
    optional: set[str],
    where: str,
    report: ValidationReport,
) -> None:
    keys = set(table)
    for key in sorted(required - keys):
        report.add(where, f"missing required key {key!r}")
    for key in sorted(keys - required - optional):
        report.add(where, f"unknown key {key!r}")


def _str(value: object, field: str, where: str, report: ValidationReport) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        report.add(where, f"{field} must be a non-empty string")
        return None
    return value.strip()


def _date(value: object, field: str, where: str, report: ValidationReport) -> date | None:
    if value is None:
        return None
    # TOML dates parse natively; a quoted string is a common editing slip, so
    # accept ISO strings too rather than failing on a harmless difference.
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            report.add(where, f"{field} must be an ISO date (YYYY-MM-DD), got {value!r}")
            return None
    report.add(where, f"{field} must be a date")
    return None


def _enum[E: StrEnum](value: object, enum: type[E], field: str, where: str, report: ValidationReport) -> E | None:
    if value is None:
        return None
    if not isinstance(value, str):
        report.add(where, f"{field} must be a string")
        return None
    try:
        return enum(value)
    except ValueError:
        allowed = ", ".join(member.value for member in enum)
        report.add(where, f"{field} {value!r} is not one of: {allowed}")
        return None


def _enum_list[E: StrEnum](
    value: object, enum: type[E], field: str, where: str, report: ValidationReport
) -> tuple[E, ...]:
    if not isinstance(value, list):
        report.add(where, f"{field} must be an array")
        return ()
    parsed: list[E] = []
    for item in value:
        member = _enum(item, enum, field, where, report)
        if member is not None:
            parsed.append(member)
    return tuple(parsed)


def _str_list(value: object, field: str, where: str, report: ValidationReport) -> tuple[str, ...]:
    if not isinstance(value, list):
        report.add(where, f"{field} must be an array of strings")
        return ()
    items: list[str] = []
    for item in value:
        if not isinstance(item, str):
            report.add(where, f"{field} must contain only strings")
            continue
        items.append(item)
    return tuple(items)


def _parse_features(
    value: object, taxonomy: Taxonomy, where: str, report: ValidationReport
) -> dict[str, FeatureValue]:
    if not isinstance(value, dict):
        report.add(where, "[features] must be a table")
        return {}
    features: dict[str, FeatureValue] = {}
    for key, raw in value.items():
        if key not in taxonomy.feature_ids:
            report.add(where, f"[features] references unknown feature {key!r}")
            continue
        try:
            features[key] = FeatureValue.parse(raw)
        except ValueError as exc:
            report.add(where, f"[features].{key}: {exc}")
    return features


def _parse_links(raw: dict[str, object], where: str, report: ValidationReport) -> tuple[Link, ...]:
    """Parse both link forms of spec 9 into the canonical list form.

    `[links]` as a table maps one URL per type; `[[links]]` as an array of tables
    allows repeats and labels. Supporting both now means the eventual migration
    to the richer form is a data edit with no code change (spec 9).
    """
    links: list[Link] = []
    value = raw.get("links")

    # `homepage = "..."` at the top level is a convenience shorthand; fold it in
    # so downstream code only ever looks at `links`.
    homepage = raw.get("homepage")
    if homepage is not None:
        url = _str(homepage, "homepage", where, report)
        if url and _check_url(url, "homepage", where, report):
            links.append(Link(type="homepage", url=url))

    if value is None:
        pass
    elif isinstance(value, dict):
        for link_type, url_value in value.items():
            if link_type not in LINK_TYPES:
                report.add(where, f"[links] has unknown link type {link_type!r}")
                continue
            url = _str(url_value, f"links.{link_type}", where, report)
            if url and _check_url(url, f"links.{link_type}", where, report):
                links.append(Link(type=link_type, url=url))
    elif isinstance(value, list):
        for index, row in enumerate(value):
            entry = f"links[{index}]"
            if not isinstance(row, dict):
                report.add(where, f"{entry} must be a table")
                continue
            _check_keys(row, required={"type", "url"}, optional={"label", "check"}, where=f"{where} {entry}", report=report)
            link_type = _str(row.get("type"), f"{entry}.type", where, report)
            url = _str(row.get("url"), f"{entry}.url", where, report)
            if link_type is None or url is None:
                continue
            if link_type not in LINK_TYPES:
                report.add(where, f"{entry} has unknown link type {link_type!r}")
                continue
            if not _check_url(url, f"{entry}.url", where, report):
                continue
            label = _str(row.get("label"), f"{entry}.label", where, report) if "label" in row else None
            links.append(Link(type=link_type, url=url, label=label, check=bool(row.get("check", True))))
    else:
        report.add(where, "links must be a table or an array of tables")

    # A homepage given both ways is a contradiction waiting to drift.
    seen: set[tuple[str, str]] = set()
    unique: list[Link] = []
    for link in links:
        key = (link.type, link.url)
        if key in seen:
            report.add(where, f"duplicate {link.type} link {link.url!r}")
            continue
        seen.add(key)
        unique.append(link)
    return tuple(unique)


def _check_url(url: str, field: str, where: str, report: ValidationReport) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        report.add(where, f"{field} must be an http(s) URL, got {url!r}")
        return False
    if not parsed.netloc:
        report.add(where, f"{field} has no host: {url!r}")
        return False
    return True


def _parse_screenshots(value: object, where: str, report: ValidationReport) -> tuple[Screenshot, ...]:
    if not isinstance(value, list):
        report.add(where, "screenshots must be an array of tables")
        return ()
    shots: list[Screenshot] = []
    for index, row in enumerate(value):
        entry = f"screenshots[{index}]"
        if not isinstance(row, dict):
            report.add(where, f"{entry} must be a table")
            continue
        _check_keys(
            row,
            required={"path"},
            optional={"caption", "source_url", "captured_at"},
            where=f"{where} {entry}",
            report=report,
        )
        path = _str(row.get("path"), f"{entry}.path", where, report)
        if path is None:
            continue
        shots.append(
            Screenshot(
                path=path,
                caption=_str(row.get("caption"), f"{entry}.caption", where, report) if "caption" in row else None,
                source_url=_str(row.get("source_url"), f"{entry}.source_url", where, report)
                if "source_url" in row
                else None,
                captured_at=_date(row.get("captured_at"), f"{entry}.captured_at", where, report)
                if "captured_at" in row
                else None,
            )
        )
    return tuple(shots)


def _parse_prose(value: object, where: str, report: ValidationReport) -> Prose:
    if not isinstance(value, dict):
        report.add(where, "[review] must be a table")
        return Prose()
    _check_keys(value, required=set(), optional={"generated_file", "override_file"}, where=where, report=report)
    return Prose(
        generated_file=_str(value.get("generated_file"), "review.generated_file", where, report)
        if "generated_file" in value
        else None,
        override_file=_str(value.get("override_file"), "review.override_file", where, report)
        if "override_file" in value
        else None,
    )


# --- cross-field and cross-record checks -----------------------------------


def _validate_combinations(
    *,
    where: str,
    report: ValidationReport,
    lifecycle: Lifecycle,
    source_model: SourceModel,
    licence: str | None,
    links: tuple[Link, ...],
    discontinued_at: date | None,
    discontinued_evidence: str | None,
) -> None:
    """Checks that need more than one field (spec 24)."""
    link_types = {link.type for link in links}

    # Source availability and licence are separate facts, but some pairings are
    # incoherent rather than merely incomplete (spec 11).
    if source_model is SourceModel.OPEN_SOURCE and not licence:
        report.add(where, "source_model is open-source but no license is recorded")
    if source_model is SourceModel.CLOSED_SOURCE and licence:
        report.add(where, "source_model is closed-source but a license is recorded")
    if source_model in (SourceModel.OPEN_SOURCE, SourceModel.HYBRID) and "source" not in link_types:
        report.add(where, f"source_model is {source_model.value} but no source link is recorded")
    if source_model is SourceModel.CLOSED_SOURCE and "source" in link_types:
        report.add(where, "source_model is closed-source but a source link is recorded")

    # A discontinued client must carry its evidence, because the historical page
    # has to say why (spec 5.7) and because no machine signal may put it here
    # on its own (invariant 5).
    if lifecycle is Lifecycle.DISCONTINUED:
        if discontinued_at is None:
            report.add(where, "status is discontinued but discontinued_at is not recorded")
        if not discontinued_evidence:
            report.add(where, "status is discontinued but discontinued_evidence is not recorded")
    elif discontinued_at is not None or discontinued_evidence:
        report.add(where, "discontinued_at/discontinued_evidence recorded but status is not discontinued")

    if lifecycle.published and "homepage" not in link_types and "hosted" not in link_types:
        report.add(where, "a published client needs a homepage or hosted link")


def _validate_cross_references(
    clients: tuple[Client, ...] | list[Client], taxonomy: Taxonomy, report: ValidationReport
) -> None:
    """Checks that need the whole set: successor targets, prose files, comparisons."""
    slugs = {client.slug for client in clients}

    for client in clients:
        for successor in client.successors:
            if successor not in slugs:
                report.add(client.source_file, f"successors references unknown client {successor!r}")

        # A referenced prose file that does not exist would render as a silently
        # empty review (spec 24: "references to missing source files").
        for label, relative in (
            ("review.generated_file", client.prose.generated_file),
            ("review.override_file", client.prose.override_file),
        ):
            if relative is None:
                continue
            path = Path(client.source_file).parents[2] / relative
            if not path.exists():
                report.add(client.source_file, f"{label} points at missing file {relative!r}")

    for comparison in taxonomy.comparisons:
        for slug in (comparison.left, comparison.right):
            if slug not in slugs:
                report.add("comparisons.toml", f"comparison references unknown client {slug!r}")
