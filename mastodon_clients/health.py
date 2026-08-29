"""Synthesis of a maintenance status from machine observations (spec 14).

The rules here are deliberately conservative and deliberately boring. The one
requirement that shapes all of them is invariant 5:

    A single machine signal cannot declare a project abandoned.

So every downgrade below `LOW_ACTIVITY` needs corroboration from an independent
signal, and a dead domain on its own never reaches `UNMAINTAINED` -- it produces
a warning for a human instead (spec 38).

`DISCONTINUED` is not derivable at all. It comes only from the editorial
lifecycle field, which no observation may write (spec 33).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from mastodon_clients.models import Client, Health, Lifecycle, Observation

# Activity thresholds in days. Chosen to be defensible rather than precise: a
# six-month-old commit on a mature, feature-complete client is not a problem,
# which is why the low-activity band is wide.
_ACTIVE_DAYS = 90
_MAINTAINED_DAYS = 270
_LOW_ACTIVITY_DAYS = 540


@dataclass(frozen=True, slots=True)
class Warning_:
    """A condition worth a human's attention (spec 38).

    Warnings never change a status by themselves. They exist so that a refresh
    can say "look at this" without the system drawing the conclusion.
    """

    client: str
    message: str


@dataclass(frozen=True, slots=True)
class HealthResult:
    """A derived status plus the reasoning behind it.

    `reasons` is rendered on the client page so a reader can see why a status was
    assigned (spec 14: "make the underlying observations visible").
    """

    status: Health
    reasons: tuple[str, ...]
    warnings: tuple[Warning_, ...]


@dataclass(frozen=True, slots=True)
class ObservationSet:
    """Every observation for one client, indexed by signal."""

    client: str
    by_signal: dict[str, Observation]
    updated_at: str | None = None

    def get(self, signal: str) -> Observation | None:
        return self.by_signal.get(signal)

    def value(self, signal: str, key: str) -> object | None:
        observation = self.by_signal.get(signal)
        if observation is None or not observation.ok:
            return None
        return observation.value.get(key)

    def date_value(self, signal: str, key: str) -> date | None:
        raw = self.value(signal, key)
        if not isinstance(raw, str):
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
        except ValueError:
            return None


OBSERVATIONS_PATH = Path("data") / "generated" / "observations.json"


def load_observations(root: Path) -> dict[str, ObservationSet]:
    """Read the committed observation file.

    Absence is normal, not an error: a repository with no refresh yet still
    builds, every client simply reads as `UNKNOWN` (spec 44).
    """
    path = root / OBSERVATIONS_PATH
    if not path.is_file():
        return {}

    raw = json.loads(path.read_text(encoding="utf-8"))
    updated_at = raw.get("updated_at")
    sets: dict[str, dict[str, Observation]] = {}
    for row in raw.get("observations", []):
        observation = Observation(
            client=row["client"],
            signal=row["signal"],
            observed_at=row["observed_at"],
            source=row.get("source", "unknown"),
            ok=bool(row.get("ok", False)),
            value=row.get("value") or {},
            error=row.get("error"),
        )
        sets.setdefault(observation.client, {})[observation.signal] = observation

    return {
        slug: ObservationSet(client=slug, by_signal=signals, updated_at=updated_at) for slug, signals in sets.items()
    }


def derive(client: Client, observations: ObservationSet | None, today: date | None = None) -> HealthResult:
    """Derive a maintenance status for one client.

    Pure and deterministic given `today`, which the site build pins to the most
    recent observation date rather than the wall clock, so two builds of the same
    commit agree (spec 44).
    """
    today = today or datetime.now(UTC).date()
    reasons: list[str] = []
    warnings: list[Warning_] = []

    # Editorial lifecycle wins outright. A human said this project is over; no
    # amount of signal activity overrides that, and no absence of signal
    # produces it (spec 33, 47).
    if client.lifecycle is Lifecycle.DISCONTINUED:
        return HealthResult(
            status=Health.DISCONTINUED,
            reasons=("Recorded as discontinued by the site editor.",),
            warnings=(),
        )

    if observations is None or not observations.by_signal:
        return HealthResult(
            status=Health.UNKNOWN,
            reasons=("No automated signals have been collected for this client yet.",),
            warnings=(),
        )

    commit = observations.date_value("repo_latest_commit", "committed_at")
    release = observations.date_value("repo_latest_release", "published_at")
    archived = observations.value("repo_archived", "archived") is True
    repo_missing = _signal_failed(observations, "repo_metadata")
    homepage_down = _signal_failed(observations, "homepage_http")
    hosted_down = _signal_failed(observations, "hosted_http")

    commit_age = (today - commit).days if commit else None
    release_age = (today - release).days if release else None

    if commit is not None:
        reasons.append(f"Latest commit {commit.isoformat()} ({commit_age} days ago).")
    if release is not None:
        reasons.append(f"Latest release {release.isoformat()} ({release_age} days ago).")

    # --- warnings (never conclusions) --------------------------------------
    if archived:
        warnings.append(Warning_(client.slug, "Source repository is archived."))
    if repo_missing:
        warnings.append(Warning_(client.slug, "Source repository could not be reached or no longer exists."))
    if homepage_down:
        warnings.append(Warning_(client.slug, "Homepage was unreachable at the last check."))
    if hosted_down:
        warnings.append(Warning_(client.slug, "Hosted application was unreachable at the last check."))
    if (
        commit_age is not None
        and release_age is not None
        and commit_age > _LOW_ACTIVITY_DAYS
        and release_age > _LOW_ACTIVITY_DAYS
    ):
        warnings.append(Warning_(client.slug, "No commit and no release for over eighteen months; review recommended."))

    # --- status ------------------------------------------------------------
    # An archived repository is an explicit statement by the maintainer, so it
    # counts as one strong signal -- but still needs corroboration to reach
    # `unmaintained` (invariant 5).
    if archived:
        reasons.append("Source repository is archived.")

    if commit_age is None and release_age is None:
        # No activity data at all. Availability alone cannot establish health,
        # and a down homepage alone certainly cannot establish its absence.
        reasons.append("No repository activity data available.")
        return HealthResult(status=Health.UNKNOWN, reasons=tuple(reasons), warnings=tuple(warnings))

    freshest = min(age for age in (commit_age, release_age) if age is not None)

    if freshest <= _ACTIVE_DAYS and not archived:
        status = Health.ACTIVELY_MAINTAINED
    elif freshest <= _MAINTAINED_DAYS and not archived:
        status = Health.MAINTAINED
    elif freshest <= _LOW_ACTIVITY_DAYS:
        status = Health.LOW_ACTIVITY
    else:
        # Beyond the low-activity window. Corroboration decides how far down.
        corroborating = sum([archived, repo_missing, homepage_down and hosted_down])
        if corroborating >= 2:
            status = Health.UNMAINTAINED
            reasons.append("Long inactivity corroborated by more than one independent signal.")
        elif corroborating == 1:
            status = Health.POSSIBLY_UNMAINTAINED
            reasons.append("Long inactivity plus one corroborating signal; not treated as conclusive.")
        else:
            status = Health.POSSIBLY_UNMAINTAINED
            reasons.append("Long inactivity, but no other signal corroborates it.")

    if archived and status in (Health.LOW_ACTIVITY,):
        status = Health.POSSIBLY_UNMAINTAINED

    return HealthResult(status=status, reasons=tuple(reasons), warnings=tuple(warnings))


def _signal_failed(observations: ObservationSet, signal: str) -> bool:
    """Whether a signal was collected and came back unsuccessful.

    A signal that was never collected is not a failure. Treating absence as
    failure is exactly the mistake invariant 5 exists to prevent.
    """
    observation = observations.get(signal)
    return observation is not None and not observation.ok


def derive_all(
    clients: tuple[Client, ...],
    observations: dict[str, ObservationSet],
    today: date | None = None,
) -> dict[str, HealthResult]:
    return {client.slug: derive(client, observations.get(client.slug), today) for client in clients}
