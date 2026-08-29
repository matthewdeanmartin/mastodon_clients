"""Maintenance synthesis (spec 14, invariant 5).

The tests that matter most here are the negative ones: the cases where a signal
looks like abandonment and must not be treated as it.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from mastodon_clients.health import ObservationSet, derive, load_observations
from mastodon_clients.models import Client, Deployment, Health, Lifecycle, Observation, ServerDependency, SourceModel

TODAY = date(2026, 8, 29)


def _client(slug: str = "example", lifecycle: Lifecycle = Lifecycle.ACTIVE, **overrides) -> Client:
    defaults = {
        "slug": slug,
        "name": slug.title(),
        "summary": "For testing.",
        "lifecycle": lifecycle,
        "source_model": SourceModel.UNKNOWN,
        "deployment": Deployment.UNKNOWN,
        "server_dependency": ServerDependency.UNKNOWN,
        "reviewed_at": date(2026, 1, 1),
    }
    return Client(**{**defaults, **overrides})


def _observations(**signals: Observation) -> ObservationSet:
    return ObservationSet(client="example", by_signal=dict(signals), updated_at="2026-08-29T00:00:00Z")


def _ok(signal: str, **value) -> Observation:
    return Observation(
        client="example", signal=signal, observed_at="2026-08-29T00:00:00Z", source="test", ok=True, value=value
    )


def _failed(signal: str, error: str = "unreachable") -> Observation:
    return Observation(
        client="example", signal=signal, observed_at="2026-08-29T00:00:00Z", source="test", ok=False, error=error
    )


def _commit(days_ago: int) -> Observation:
    return _ok("repo_latest_commit", committed_at=f"{date.fromordinal(TODAY.toordinal() - days_ago)}T00:00:00Z")


# --- invariant 5: no single signal declares abandonment -------------------


def test_dead_homepage_alone_does_not_mark_a_client_discontinued() -> None:
    """Acceptance criterion 14, stated directly."""
    result = derive(
        _client(),
        _observations(homepage_http=_failed("homepage_http", "HTTP 503"), repo_latest_commit=_commit(10)),
        TODAY,
    )
    assert result.status is not Health.DISCONTINUED
    assert result.status is not Health.UNMAINTAINED
    assert result.status is Health.ACTIVELY_MAINTAINED


def test_dead_homepage_with_no_activity_data_yields_unknown() -> None:
    """A failing link says nothing about whether the software is maintained."""
    result = derive(_client(), _observations(homepage_http=_failed("homepage_http")), TODAY)
    assert result.status is Health.UNKNOWN


def test_long_inactivity_alone_does_not_reach_unmaintained() -> None:
    """Some software stops changing because it is finished."""
    result = derive(_client(), _observations(repo_latest_commit=_commit(900)), TODAY)
    assert result.status is Health.POSSIBLY_UNMAINTAINED
    assert "no other signal corroborates" in " ".join(result.reasons)


def test_archived_repository_alone_does_not_reach_unmaintained() -> None:
    """Archiving may mean development moved rather than stopped."""
    result = derive(
        _client(),
        _observations(repo_archived=_ok("repo_archived", archived=True), repo_latest_commit=_commit(900)),
        TODAY,
    )
    assert result.status is Health.POSSIBLY_UNMAINTAINED


def test_two_corroborating_signals_can_reach_unmaintained() -> None:
    """Corroboration is what the bar requires -- and here it is met."""
    result = derive(
        _client(),
        _observations(
            repo_latest_commit=_commit(900),
            repo_archived=_ok("repo_archived", archived=True),
            repo_metadata=_failed("repo_metadata", "HTTP 404"),
        ),
        TODAY,
    )
    assert result.status is Health.UNMAINTAINED


def test_discontinued_comes_only_from_the_editorial_field() -> None:
    """No observation may write the lifecycle field (spec 33)."""
    result = derive(_client(lifecycle=Lifecycle.DISCONTINUED), _observations(repo_latest_commit=_commit(1)), TODAY)
    assert result.status is Health.DISCONTINUED


def test_no_observations_is_unknown_not_unmaintained() -> None:
    result = derive(_client(), None, TODAY)
    assert result.status is Health.UNKNOWN


def test_a_signal_never_collected_is_not_a_failure() -> None:
    """Absence must not be read as failure -- that is the invariant-5 mistake."""
    with_absent = derive(_client(), _observations(repo_latest_commit=_commit(900)), TODAY)
    with_failed = derive(
        _client(),
        _observations(repo_latest_commit=_commit(900), repo_metadata=_failed("repo_metadata")),
        TODAY,
    )
    # The one with an actual failure is downgraded; the one with a missing
    # signal is not.
    assert with_absent.status is Health.POSSIBLY_UNMAINTAINED
    assert "no other signal corroborates" in " ".join(with_absent.reasons)
    assert "one corroborating signal" in " ".join(with_failed.reasons)


# --- ordinary activity bands ----------------------------------------------


def test_recent_commit_is_actively_maintained() -> None:
    assert derive(_client(), _observations(repo_latest_commit=_commit(5)), TODAY).status is Health.ACTIVELY_MAINTAINED


def test_moderately_recent_commit_is_maintained() -> None:
    assert derive(_client(), _observations(repo_latest_commit=_commit(150)), TODAY).status is Health.MAINTAINED


def test_quiet_but_not_silent_is_low_activity() -> None:
    assert derive(_client(), _observations(repo_latest_commit=_commit(400)), TODAY).status is Health.LOW_ACTIVITY


def test_a_recent_release_counts_even_with_an_old_commit() -> None:
    """The freshest signal wins; a tagged release is activity."""
    result = derive(
        _client(),
        _observations(
            repo_latest_commit=_commit(600),
            repo_latest_release=_ok("repo_latest_release", published_at="2026-08-01T00:00:00Z"),
        ),
        TODAY,
    )
    assert result.status is Health.ACTIVELY_MAINTAINED


# --- warnings are not conclusions (spec 38) -------------------------------


def test_conditions_produce_warnings_without_changing_status() -> None:
    result = derive(
        _client(),
        _observations(
            repo_latest_commit=_commit(5),
            repo_archived=_ok("repo_archived", archived=True),
            homepage_http=_failed("homepage_http"),
        ),
        TODAY,
    )
    messages = " ".join(warning.message for warning in result.warnings)
    assert "archived" in messages
    assert "Homepage was unreachable" in messages
    # Archived caps the status, but the failing homepage did not drive it down.
    assert result.status is not Health.UNMAINTAINED


def test_reasons_are_exposed_for_the_reader() -> None:
    """Spec 14 requires the underlying observations be visible."""
    result = derive(_client(), _observations(repo_latest_commit=_commit(30)), TODAY)
    assert result.reasons
    assert any("Latest commit" in reason for reason in result.reasons)


# --- persistence ----------------------------------------------------------


def test_missing_observation_file_is_not_an_error(repo: Path) -> None:
    """A repository with no refresh yet still builds (spec 44)."""
    assert load_observations(repo) == {}


def test_observations_round_trip(repo: Path, write_observations) -> None:
    write_observations(
        "2026-08-29T12:00:00Z",
        [
            {
                "client": "alpha",
                "signal": "homepage_http",
                "observed_at": "2026-08-29T12:00:00Z",
                "source": "http",
                "ok": True,
                "value": {"status": 200},
                "error": None,
            }
        ],
    )
    loaded = load_observations(repo)
    assert "alpha" in loaded
    assert loaded["alpha"].value("homepage_http", "status") == 200
    assert loaded["alpha"].updated_at == "2026-08-29T12:00:00Z"
