"""Deterministic scoring (spec 17, 44)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from mawkingbird.errors import ValidationReport
from mawkingbird.models import Client, Deployment, FeatureValue, Health, Lifecycle, Link, ServerDependency, SourceModel
from mawkingbird.schema import load_clients
from mawkingbird.scoring import TOTAL_MAX, Score, describe_components, score_client
from mawkingbird.taxonomy import load_taxonomy


def _taxonomy(repo: Path):
    return load_taxonomy(repo, ValidationReport())


def _clients(repo: Path):
    report = ValidationReport()
    taxonomy = load_taxonomy(repo, report)
    return load_clients(repo, taxonomy, report), taxonomy


def _points(score: Score, component_id: str) -> float:
    """A component's points, asserting the component exists.

    `Score.component()` returns None for an unknown id; a test that silently
    compared None to None would pass while checking nothing.
    """
    component = score.component(component_id)
    assert component is not None, f"no component {component_id!r}"
    return float(component.points)


def _bare(**overrides) -> Client:
    """A client with nothing recorded, for isolating one component at a time."""
    defaults = {
        "slug": "bare",
        "name": "Bare",
        "summary": "Nothing recorded.",
        "lifecycle": Lifecycle.ACTIVE,
        "source_model": SourceModel.UNKNOWN,
        "deployment": Deployment.UNKNOWN,
        "server_dependency": ServerDependency.UNKNOWN,
        "reviewed_at": date(2026, 1, 1),
    }
    return Client(**{**defaults, **overrides})


def test_scoring_is_deterministic(repo: Path) -> None:
    """Two runs over the same data must agree, or the site is not reproducible."""
    clients, taxonomy = _clients(repo)
    first = [score_client(c, taxonomy, Health.MAINTAINED) for c in clients]
    second = [score_client(c, taxonomy, Health.MAINTAINED) for c in clients]
    assert [s.points for s in first] == [s.points for s in second]
    assert [s.stars for s in first] == [s.stars for s in second]


def test_components_sum_to_the_published_total(repo: Path) -> None:
    """The methodology page's total must match what the code can actually award."""
    assert sum(c.maximum for c in describe_components()) == TOTAL_MAX == 100


def test_stars_land_on_half_steps(repo: Path) -> None:
    clients, taxonomy = _clients(repo)
    for client in clients:
        stars = score_client(client, taxonomy, Health.MAINTAINED).stars
        assert 0 <= stars <= 5
        assert (stars * 2) == int(stars * 2)


def test_partial_earns_half_a_feature_point(repo: Path) -> None:
    taxonomy = _taxonomy(repo)
    core = {f.id for f in taxonomy.core_features}

    full = _bare(features=dict.fromkeys(core, FeatureValue.YES))
    half = _bare(features=dict.fromkeys(core, FeatureValue.PARTIAL))
    none = _bare(features=dict.fromkeys(core, FeatureValue.NO))

    full_points = _points(score_client(full, taxonomy, Health.UNKNOWN), "feature_breadth")
    half_points = _points(score_client(half, taxonomy, Health.UNKNOWN), "feature_breadth")
    none_points = _points(score_client(none, taxonomy, Health.UNKNOWN), "feature_breadth")

    assert none_points == 0
    assert half_points == full_points / 2


def test_unknown_features_lower_the_score_and_are_counted(repo: Path) -> None:
    """Missing information does lower a score -- and is reported, so a reader
    can tell an under-researched client from a limited one."""
    taxonomy = _taxonomy(repo)
    core = {f.id for f in taxonomy.core_features}

    known = _bare(features=dict.fromkeys(core, FeatureValue.YES))
    unknown = _bare(features=dict.fromkeys(core, FeatureValue.UNKNOWN))

    known_score = score_client(known, taxonomy, Health.UNKNOWN)
    unknown_score = score_client(unknown, taxonomy, Health.UNKNOWN)

    assert unknown_score.points < known_score.points
    assert unknown_score.unknown_features == len(core)
    assert known_score.unknown_features == 0


def test_not_applicable_leaves_the_denominator(repo: Path) -> None:
    """A feature that cannot apply must not be counted against the client."""
    taxonomy = _taxonomy(repo)
    core = [f.id for f in taxonomy.core_features]

    all_yes = _bare(features=dict.fromkeys(core, FeatureValue.YES))
    one_na = _bare(
        features={**dict.fromkeys(core, FeatureValue.YES), core[0]: FeatureValue.NOT_APPLICABLE},
    )

    # Both are "everything that applies is supported", so both score full marks.
    assert (
        _points(score_client(one_na, taxonomy, Health.UNKNOWN), "feature_breadth")
        == _points(score_client(all_yes, taxonomy, Health.UNKNOWN), "feature_breadth")
    )


def test_non_core_features_do_not_reduce_breadth(repo: Path) -> None:
    taxonomy = _taxonomy(repo)
    core = {f.id for f in taxonomy.core_features}

    without = _bare(features=dict.fromkeys(core, FeatureValue.YES))
    with_no_extra = _bare(features={**dict.fromkeys(core, FeatureValue.YES), "column_layout": FeatureValue.NO})

    assert (
        _points(score_client(with_no_extra, taxonomy, Health.UNKNOWN), "feature_breadth")
        == _points(score_client(without, taxonomy, Health.UNKNOWN), "feature_breadth")
    )


def test_maintenance_points_follow_health(repo: Path) -> None:
    taxonomy = _taxonomy(repo)
    client = _bare()

    ordered = [
        Health.ACTIVELY_MAINTAINED,
        Health.MAINTAINED,
        Health.LOW_ACTIVITY,
        Health.POSSIBLY_UNMAINTAINED,
        Health.UNMAINTAINED,
    ]
    points = [_points(score_client(client, taxonomy, h), "maintenance") for h in ordered]
    assert points == sorted(points, reverse=True)


def test_unknown_health_is_not_scored_as_abandonment(repo: Path) -> None:
    """Absent evidence is not evidence of abandonment (invariant 5)."""
    taxonomy = _taxonomy(repo)
    client = _bare()
    unknown = _points(score_client(client, taxonomy, Health.UNKNOWN), "maintenance")
    unmaintained = _points(score_client(client, taxonomy, Health.UNMAINTAINED), "maintenance")
    assert unknown > unmaintained


def test_documentation_and_support_links_earn_points(repo: Path) -> None:
    taxonomy = _taxonomy(repo)
    bare = _bare(deployment=Deployment.SELF_HOSTABLE)
    documented = _bare(
        deployment=Deployment.SELF_HOSTABLE,
        links=(
            Link(type="documentation", url="https://docs.example.com/"),
            Link(type="source", url="https://github.com/example/x"),
            Link(type="issues", url="https://github.com/example/x/issues"),
        ),
    )

    assert (
        _points(score_client(documented, taxonomy, Health.UNKNOWN), "deployment_docs")
        > _points(score_client(bare, taxonomy, Health.UNKNOWN), "deployment_docs")
    )
    assert (
        _points(score_client(documented, taxonomy, Health.UNKNOWN), "support")
        > _points(score_client(bare, taxonomy, Health.UNKNOWN), "support")
    )


def test_no_component_can_exceed_its_maximum(repo: Path) -> None:
    """A client with everything recorded must still land inside the scale."""
    taxonomy = _taxonomy(repo)
    everything = _bare(
        source_model=SourceModel.OPEN_SOURCE,
        deployment=Deployment.HOSTED_AND_SELF_HOSTABLE,
        licence="MIT",
        features=dict.fromkeys((f.id for f in taxonomy.features), FeatureValue.YES),
        links=tuple(
            Link(type=t, url=f"https://example.com/{t}")
            for t in ("homepage", "documentation", "source", "issues", "support", "community", "changelog")
        ),
    )
    score = score_client(everything, taxonomy, Health.ACTIVELY_MAINTAINED)
    for component in score.components:
        assert component.points <= component.maximum
    assert score.points <= TOTAL_MAX
    assert score.stars == 5.0
