"""Loading and validation of the controlled vocabularies in `data/taxonomy/`.

The taxonomy is what makes "unknown feature identifier" and "nonexistent
taxonomy value" detectable (spec 24). Client records are checked against it
rather than against a hard-coded list in the schema module, so extending the
vocabulary is a data edit.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from mastodon_clients.errors import ValidationReport

# Feature ids grouped as accessibility-related, for the accessibility scoring
# component (spec 17). Named here rather than flagged per-feature because the
# grouping is a scoring decision, not a property of the feature itself.
ACCESSIBILITY_FEATURE_IDS: frozenset[str] = frozenset(
    {
        "keyboard_navigation",
        "accessibility_features",
        "content_warnings",
        "reduced_motion",
        "responsive_layout",
    }
)


@dataclass(frozen=True, slots=True)
class Feature:
    """One entry in the feature taxonomy (spec 10)."""

    id: str
    label: str
    description: str
    # Whether the feature counts toward the feature-breadth score. Niche
    # features are recorded but do not penalise a client that omits them.
    core: bool = True
    # Whether the feature gets a `/features/<id>/` landing page. Only features
    # with real navigational value do (spec 39).
    page: bool = False

    @property
    def url(self) -> str:
        return f"/features/{self.id.replace('_', '-')}/"


@dataclass(frozen=True, slots=True)
class Audience:
    """One audience landing page (spec 5.4)."""

    id: str
    label: str
    intro: str
    # Feature ids that matter most to this audience; rendered as criteria and
    # used to order the matching clients.
    criteria: tuple[str, ...] = ()

    @property
    def url(self) -> str:
        return f"/for/{self.id}/"


@dataclass(frozen=True, slots=True)
class Comparison:
    """An allow-listed comparison pair (spec 5.6).

    Comparisons exist only for pairs recorded here. The quadratic set is
    deliberately not generated (invariant 8).
    """

    left: str
    right: str

    @property
    def url(self) -> str:
        return f"/compare/{self.left}/{self.right}/"


@dataclass(frozen=True, slots=True)
class Taxonomy:
    """Every controlled vocabulary, loaded once per build."""

    features: tuple[Feature, ...]
    audiences: tuple[Audience, ...]
    comparisons: tuple[Comparison, ...]

    @property
    def feature_ids(self) -> frozenset[str]:
        return frozenset(feature.id for feature in self.features)

    @property
    def audience_ids(self) -> frozenset[str]:
        return frozenset(audience.id for audience in self.audiences)

    @property
    def core_features(self) -> tuple[Feature, ...]:
        return tuple(feature for feature in self.features if feature.core)

    @property
    def page_features(self) -> tuple[Feature, ...]:
        return tuple(feature for feature in self.features if feature.page)

    def feature(self, feature_id: str) -> Feature | None:
        for feature in self.features:
            if feature.id == feature_id:
                return feature
        return None

    def audience(self, audience_id: str) -> Audience | None:
        for audience in self.audiences:
            if audience.id == audience_id:
                return audience
        return None


def _read_toml(path: Path) -> dict[str, object]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _require_keys(
    table: dict[str, object],
    *,
    required: set[str],
    optional: set[str],
    where: str,
    report: ValidationReport,
) -> bool:
    """Check a table's keys. Unknown keys are an error, not a pass-through (spec 8)."""
    keys = set(table)
    missing = required - keys
    unknown = keys - required - optional
    for key in sorted(missing):
        report.add(where, f"missing required key {key!r}")
    for key in sorted(unknown):
        report.add(where, f"unknown key {key!r}")
    return not missing and not unknown


def load_taxonomy(root: Path, report: ValidationReport | None = None) -> Taxonomy:
    """Load `data/taxonomy/` from a repository root.

    Problems are recorded in `report` when one is supplied; entries that fail to
    parse are skipped so a single malformed row does not hide the rest.
    """
    report = report if report is not None else ValidationReport()
    directory = root / "data" / "taxonomy"

    features = _load_features(directory / "features.toml", report)
    audiences = _load_audiences(directory / "audiences.toml", report)
    comparisons = _load_comparisons(directory / "comparisons.toml", report)
    return Taxonomy(features=features, audiences=audiences, comparisons=comparisons)


def _load_features(path: Path, report: ValidationReport) -> tuple[Feature, ...]:
    if not path.is_file():
        report.add(str(path), "missing feature taxonomy")
        return ()
    raw = _read_toml(path)
    rows = raw.get("feature", [])
    if not isinstance(rows, list):
        report.add(str(path), "expected an array of [[feature]] tables")
        return ()

    features: list[Feature] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        where = f"{path}[feature.{index}]"
        if not isinstance(row, dict):
            report.add(where, "expected a table")
            continue
        if not _require_keys(
            row,
            required={"id", "label", "description"},
            optional={"core", "page"},
            where=where,
            report=report,
        ):
            continue
        feature_id = str(row["id"])
        if feature_id in seen:
            report.add(where, f"duplicate feature id {feature_id!r}")
            continue
        seen.add(feature_id)
        features.append(
            Feature(
                id=feature_id,
                label=str(row["label"]),
                description=str(row["description"]),
                core=bool(row.get("core", True)),
                page=bool(row.get("page", False)),
            )
        )
    return tuple(features)


def _load_audiences(path: Path, report: ValidationReport) -> tuple[Audience, ...]:
    if not path.is_file():
        report.add(str(path), "missing audience taxonomy")
        return ()
    raw = _read_toml(path)
    rows = raw.get("audience", [])
    if not isinstance(rows, list):
        report.add(str(path), "expected an array of [[audience]] tables")
        return ()

    audiences: list[Audience] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        where = f"{path}[audience.{index}]"
        if not isinstance(row, dict):
            report.add(where, "expected a table")
            continue
        if not _require_keys(
            row,
            required={"id", "label", "intro"},
            optional={"criteria"},
            where=where,
            report=report,
        ):
            continue
        audience_id = str(row["id"])
        if audience_id in seen:
            report.add(where, f"duplicate audience id {audience_id!r}")
            continue
        seen.add(audience_id)
        criteria = row.get("criteria", [])
        if not isinstance(criteria, list):
            report.add(where, "criteria must be an array of feature ids")
            criteria = []
        audiences.append(
            Audience(
                id=audience_id,
                label=str(row["label"]),
                intro=str(row["intro"]).strip(),
                criteria=tuple(str(item) for item in criteria),
            )
        )
    return tuple(audiences)


def _load_comparisons(path: Path, report: ValidationReport) -> tuple[Comparison, ...]:
    # Comparisons are optional: an empty allow-list means no comparison pages.
    if not path.is_file():
        return ()
    raw = _read_toml(path)
    rows = raw.get("comparison", [])
    if not isinstance(rows, list):
        report.add(str(path), "expected an array of [[comparison]] tables")
        return ()

    comparisons: list[Comparison] = []
    for index, row in enumerate(rows):
        where = f"{path}[comparison.{index}]"
        if not isinstance(row, dict):
            report.add(where, "expected a table")
            continue
        if not _require_keys(row, required={"left", "right"}, optional=set(), where=where, report=report):
            continue
        left, right = str(row["left"]), str(row["right"])
        if left == right:
            report.add(where, "a comparison must name two different clients")
            continue
        comparisons.append(Comparison(left=left, right=right))
    return tuple(comparisons)


def validate_taxonomy(taxonomy: Taxonomy, report: ValidationReport) -> None:
    """Cross-checks that need the whole taxonomy loaded."""
    for audience in taxonomy.audiences:
        for feature_id in audience.criteria:
            if feature_id not in taxonomy.feature_ids:
                report.add(
                    f"audiences.toml[{audience.id}]",
                    f"criteria references unknown feature {feature_id!r}",
                )
