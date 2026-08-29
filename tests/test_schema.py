"""TOML parsing and validation (spec 8, 24)."""

from __future__ import annotations

from pathlib import Path

from mawkingbird.errors import ValidationReport
from mawkingbird.models import Deployment, FeatureValue, Lifecycle, SourceModel
from mawkingbird.schema import load_clients
from mawkingbird.taxonomy import load_taxonomy


def _load(repo: Path):
    report = ValidationReport()
    taxonomy = load_taxonomy(repo, report)
    clients = load_clients(repo, taxonomy, report)
    return clients, report


def test_valid_records_parse(repo: Path) -> None:
    clients, report = _load(repo)
    assert report.ok, report.render()
    assert [c.slug for c in clients] == ["alpha", "beta"]

    alpha = clients[0]
    assert alpha.name == "Alpha"
    assert alpha.lifecycle is Lifecycle.ACTIVE
    assert alpha.source_model is SourceModel.OPEN_SOURCE
    assert alpha.deployment is Deployment.HOSTED_AND_SELF_HOSTABLE
    assert alpha.licence == "MIT"


def test_records_are_sorted_by_slug(repo: Path, write_client) -> None:
    """Ordering must not depend on the filesystem, or output is non-deterministic."""
    write_client(
        "aardvark",
        """
        schema_version = 1
        slug = "aardvark"
        name = "Aardvark"
        summary = "First alphabetically."
        status = "active"
        reviewed_at = 2026-08-29
        source_model = "closed-source"
        deployment = "hosted"
        homepage = "https://aardvark.example.com/"
        """,
    )
    clients, report = _load(repo)
    assert report.ok, report.render()
    assert [c.slug for c in clients] == ["aardvark", "alpha", "beta"]


# --- unknown keys are errors, not pass-through (spec 8) --------------------


def test_unknown_top_level_key_is_an_error(repo: Path, write_client) -> None:
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "Has a typo'd key."
        status = "active"
        reviewed_at = 2026-08-29
        source_model = "closed-source"
        deployment = "hosted"
        homepage = "https://gamma.example.com/"
        licence = "MIT"
        """,
    )
    _, report = _load(repo)
    assert any("unknown key 'licence'" in str(issue) for issue in report.issues)


def test_unknown_feature_is_an_error(repo: Path, write_client) -> None:
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "References a feature that is not in the taxonomy."
        status = "active"
        reviewed_at = 2026-08-29
        source_model = "closed-source"
        deployment = "hosted"
        homepage = "https://gamma.example.com/"

        [features]
        telepathy = true
        """,
    )
    _, report = _load(repo)
    assert any("unknown feature 'telepathy'" in str(issue) for issue in report.issues)


def test_unknown_audience_is_an_error(repo: Path, write_client) -> None:
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "References an audience that does not exist."
        status = "active"
        reviewed_at = 2026-08-29
        source_model = "closed-source"
        deployment = "hosted"
        homepage = "https://gamma.example.com/"
        audiences = ["astronauts"]
        """,
    )
    _, report = _load(repo)
    assert any("unknown audience 'astronauts'" in str(issue) for issue in report.issues)


def test_unknown_link_type_is_an_error(repo: Path, write_client) -> None:
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "Has an unrecognised link type."
        status = "active"
        reviewed_at = 2026-08-29
        source_model = "closed-source"
        deployment = "hosted"

        [links]
        homepage = "https://gamma.example.com/"
        mastodon = "https://mastodon.social/@gamma"
        """,
    )
    _, report = _load(repo)
    assert any("unknown link type 'mastodon'" in str(issue) for issue in report.issues)


# --- other spec 24 conditions ---------------------------------------------


def test_duplicate_slug_is_detected(repo: Path, write_client) -> None:
    """Two records claiming one slug would collide on a single canonical URL."""
    write_client(
        "duplicate",
        """
        schema_version = 1
        slug = "alpha"
        name = "Alpha again"
        summary = "Claims a slug already taken."
        status = "active"
        reviewed_at = 2026-08-29
        source_model = "closed-source"
        deployment = "hosted"
        homepage = "https://alpha2.example.com/"
        """,
    )
    _, report = _load(repo)
    assert any("duplicate slug" in str(issue) for issue in report.issues)


def test_malformed_url_is_detected(repo: Path, write_client) -> None:
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "Has a URL that is not one."
        status = "active"
        reviewed_at = 2026-08-29
        source_model = "closed-source"
        deployment = "hosted"
        homepage = "gamma.example.com"
        """,
    )
    _, report = _load(repo)
    assert any("must be an http(s) URL" in str(issue) for issue in report.issues)


def test_invalid_status_is_detected(repo: Path, write_client) -> None:
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "Has a status outside the vocabulary."
        status = "sort-of-alive"
        reviewed_at = 2026-08-29
        source_model = "closed-source"
        deployment = "hosted"
        homepage = "https://gamma.example.com/"
        """,
    )
    _, report = _load(repo)
    assert any("is not one of" in str(issue) for issue in report.issues)


def test_invalid_date_is_detected(repo: Path, write_client) -> None:
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "Has an unparseable date."
        status = "active"
        reviewed_at = "the third of never"
        source_model = "closed-source"
        deployment = "hosted"
        homepage = "https://gamma.example.com/"
        """,
    )
    _, report = _load(repo)
    assert any("must be an ISO date" in str(issue) for issue in report.issues)


def test_filename_must_match_slug(repo: Path, write_client) -> None:
    """A mismatch makes `make generate-review CLIENT=x` ambiguous."""
    write_client(
        "wrongname",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "Filed under the wrong name."
        status = "active"
        reviewed_at = 2026-08-29
        source_model = "closed-source"
        deployment = "hosted"
        homepage = "https://gamma.example.com/"
        """,
    )
    _, report = _load(repo)
    assert any("filename does not match slug" in str(issue) for issue in report.issues)


def test_missing_required_field_is_detected(repo: Path, write_client) -> None:
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        status = "active"
        reviewed_at = 2026-08-29
        source_model = "closed-source"
        deployment = "hosted"
        homepage = "https://gamma.example.com/"
        """,
    )
    _, report = _load(repo)
    assert any("missing required key 'summary'" in str(issue) for issue in report.issues)


def test_validation_accumulates_rather_than_stopping(repo: Path, write_client) -> None:
    """An editor wants every problem at once, not one per run."""
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "Wrong in several ways at once."
        status = "imaginary"
        reviewed_at = 2026-08-29
        source_model = "closed-source"
        deployment = "teleported"
        homepage = "not-a-url"
        audiences = ["nobody"]
        """,
    )
    _, report = _load(repo)
    assert len(report.issues) >= 4


# --- source/licence combinations (spec 11, 24) ----------------------------


def test_open_source_without_licence_is_an_error(repo: Path, write_client) -> None:
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "Open source with no licence recorded."
        status = "active"
        reviewed_at = 2026-08-29
        source_model = "open-source"
        deployment = "hosted"

        [links]
        homepage = "https://gamma.example.com/"
        source = "https://github.com/example/gamma"
        """,
    )
    _, report = _load(repo)
    assert any("no license is recorded" in str(issue) for issue in report.issues)


def test_closed_source_with_licence_is_an_error(repo: Path, write_client) -> None:
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "Closed source but carries a licence."
        status = "active"
        reviewed_at = 2026-08-29
        source_model = "closed-source"
        license = "MIT"
        deployment = "hosted"
        homepage = "https://gamma.example.com/"
        """,
    )
    _, report = _load(repo)
    assert any("closed-source but a license is recorded" in str(issue) for issue in report.issues)


def test_open_source_without_source_link_is_an_error(repo: Path, write_client) -> None:
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "Open source with nowhere to get the source."
        status = "active"
        reviewed_at = 2026-08-29
        source_model = "open-source"
        license = "MIT"
        deployment = "hosted"
        homepage = "https://gamma.example.com/"
        """,
    )
    _, report = _load(repo)
    assert any("no source link is recorded" in str(issue) for issue in report.issues)


# --- discontinued records (spec 5.7) --------------------------------------


def test_discontinued_requires_evidence(repo: Path, write_client) -> None:
    """Nothing reaches `discontinued` without a recorded reason (invariant 5)."""
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "Marked discontinued with nothing to back it."
        status = "discontinued"
        reviewed_at = 2026-08-29
        source_model = "closed-source"
        deployment = "hosted"
        homepage = "https://gamma.example.com/"
        """,
    )
    _, report = _load(repo)
    messages = " ".join(str(issue) for issue in report.issues)
    assert "discontinued_at is not recorded" in messages
    assert "discontinued_evidence is not recorded" in messages


def test_discontinued_fields_require_discontinued_status(repo: Path, write_client) -> None:
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "Active, but carries discontinuation fields."
        status = "active"
        reviewed_at = 2026-08-29
        discontinued_at = 2026-01-01
        discontinued_evidence = "A blog post."
        source_model = "closed-source"
        deployment = "hosted"
        homepage = "https://gamma.example.com/"
        """,
    )
    _, report = _load(repo)
    assert any("status is not discontinued" in str(issue) for issue in report.issues)


def test_successor_must_exist(repo: Path, write_client) -> None:
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "Points at a successor that is not in the directory."
        status = "discontinued"
        reviewed_at = 2026-08-29
        discontinued_at = 2026-01-01
        discontinued_evidence = "Announced on the project's homepage."
        source_model = "closed-source"
        deployment = "hosted"
        homepage = "https://gamma.example.com/"
        successors = ["nonexistent"]
        """,
    )
    _, report = _load(repo)
    assert any("unknown client 'nonexistent'" in str(issue) for issue in report.issues)


# --- feature values (spec 10) ---------------------------------------------


def test_feature_values_normalise(repo: Path) -> None:
    clients, report = _load(repo)
    assert report.ok, report.render()
    alpha = clients[0]
    assert alpha.feature("multi_account") is FeatureValue.YES
    assert alpha.feature("column_layout") is FeatureValue.NO
    assert alpha.feature("keyboard_navigation") is FeatureValue.PARTIAL


def test_unrecorded_feature_reads_as_unknown(repo: Path, write_client) -> None:
    """Adding a feature to the taxonomy must not invalidate existing records."""
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "Records no features at all."
        status = "active"
        reviewed_at = 2026-08-29
        source_model = "closed-source"
        deployment = "hosted"
        homepage = "https://gamma.example.com/"
        """,
    )
    clients, report = _load(repo)
    assert report.ok, report.render()
    gamma = next(c for c in clients if c.slug == "gamma")
    assert gamma.feature("multi_account") is FeatureValue.UNKNOWN
    assert not gamma.has_feature("multi_account")


def test_partial_counts_as_having_the_feature_for_facets(repo: Path) -> None:
    clients, _ = _load(repo)
    alpha = clients[0]
    assert alpha.has_feature("keyboard_navigation")


def test_invalid_feature_value_is_an_error(repo: Path, write_client) -> None:
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "Uses a feature value outside the vocabulary."
        status = "active"
        reviewed_at = 2026-08-29
        source_model = "closed-source"
        deployment = "hosted"
        homepage = "https://gamma.example.com/"

        [features]
        multi_account = "sort of"
        """,
    )
    _, report = _load(repo)
    assert any("multi_account" in str(issue) for issue in report.issues)


# --- link forms (spec 9) --------------------------------------------------


def test_array_of_tables_link_form_parses(repo: Path, write_client) -> None:
    """Both link forms must work, so the eventual migration is a data edit."""
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "Uses the richer link form."
        status = "active"
        reviewed_at = 2026-08-29
        source_model = "open-source"
        license = "MIT"
        deployment = "hosted"

        [[links]]
        type = "homepage"
        url = "https://gamma.example.com/"

        [[links]]
        type = "source"
        url = "https://github.com/example/gamma"
        label = "Primary repository"

        [[links]]
        type = "source"
        url = "https://github.com/example/gamma-server"
        label = "Server component"
        """,
    )
    clients, report = _load(repo)
    assert report.ok, report.render()
    gamma = next(c for c in clients if c.slug == "gamma")
    sources = gamma.links_of("source")
    assert len(sources) == 2
    assert sources[0].label == "Primary repository"


def test_duplicate_link_is_detected(repo: Path, write_client) -> None:
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "Records the same homepage twice."
        status = "active"
        reviewed_at = 2026-08-29
        source_model = "closed-source"
        deployment = "hosted"
        homepage = "https://gamma.example.com/"

        [links]
        homepage = "https://gamma.example.com/"
        """,
    )
    _, report = _load(repo)
    assert any("duplicate homepage link" in str(issue) for issue in report.issues)


def test_missing_prose_file_is_detected(repo: Path, write_client) -> None:
    write_client(
        "gamma",
        """
        schema_version = 1
        slug = "gamma"
        name = "Gamma"
        summary = "Points at a prose file that is not there."
        status = "active"
        reviewed_at = 2026-08-29
        source_model = "closed-source"
        deployment = "hosted"
        homepage = "https://gamma.example.com/"

        [review]
        generated_file = "content/generated/clients/gamma.md"
        """,
    )
    _, report = _load(repo)
    assert any("points at missing file" in str(issue) for issue in report.issues)
