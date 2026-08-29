"""One assembled view of the repository's data.

Every command -- validate, score, build-content, refresh-metadata -- starts by
loading this. Assembling it in one place is what keeps the canonical data rule
(spec 47) enforceable: structured TOML first, then overrides, then observations,
then generated prose, with each layer unable to overwrite the one above it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from mawkingbird.errors import ValidationReport
from mawkingbird.health import HealthResult, ObservationSet, Warning_, derive_all, load_observations
from mawkingbird.models import Client, Deployment, Health, Lifecycle, ServerDependency, SourceModel
from mawkingbird.overrides import ProseDocument, load_prose
from mawkingbird.schema import load_clients
from mawkingbird.scoring import Score, score_all
from mawkingbird.taxonomy import Taxonomy, load_taxonomy, validate_taxonomy


@dataclass(frozen=True, slots=True)
class Site:
    """The whole dataset, validated and joined."""

    root: Path
    taxonomy: Taxonomy
    clients: tuple[Client, ...]
    observations: dict[str, ObservationSet]
    health: dict[str, HealthResult]
    scores: dict[str, Score]
    prose: dict[str, ProseDocument]
    report: ValidationReport
    observations_updated_at: str | None

    # --- selections used by page generation --------------------------------

    @property
    def published(self) -> tuple[Client, ...]:
        """Clients with an ordinary review page, alphabetically."""
        return tuple(sorted((c for c in self.clients if c.lifecycle.published), key=lambda c: c.name.lower()))

    @property
    def historical(self) -> tuple[Client, ...]:
        """Discontinued clients, which keep their URL with a historical page."""
        return tuple(sorted((c for c in self.clients if c.lifecycle.historical), key=lambda c: c.name.lower()))

    @property
    def listed(self) -> tuple[Client, ...]:
        """Everything the directory shows: published plus discontinued.

        `candidate` and `excluded` records are deliberately absent -- they exist
        so the repository can hold a decision without publishing it (spec 33).
        """
        return tuple(sorted((*self.published, *self.historical), key=lambda c: c.name.lower()))

    def client(self, slug: str) -> Client | None:
        for client in self.clients:
            if client.slug == slug:
                return client
        return None

    def status_of(self, slug: str) -> Health:
        result = self.health.get(slug)
        return result.status if result else Health.UNKNOWN

    def by_audience(self, audience_id: str) -> tuple[Client, ...]:
        return tuple(c for c in self.listed if audience_id in c.audiences)

    def by_feature(self, feature_id: str) -> tuple[Client, ...]:
        return tuple(c for c in self.listed if c.has_feature(feature_id))

    def by_source_model(self, source_model: SourceModel) -> tuple[Client, ...]:
        return tuple(c for c in self.listed if c.source_model is source_model)

    def by_deployment(self, *deployments: Deployment) -> tuple[Client, ...]:
        return tuple(c for c in self.listed if c.deployment in deployments)

    def standalone(self) -> tuple[Client, ...]:
        return tuple(c for c in self.listed if c.server_dependency is ServerDependency.INDEPENDENT)

    @property
    def warnings(self) -> tuple[Warning_, ...]:
        """Every health warning, for the refresh report (spec 38)."""
        return tuple(warning for result in self.health.values() for warning in result.warnings)

    def related(self, client: Client, limit: int = 4) -> tuple[Client, ...]:
        """Clients a reader weighing this one might also consider.

        Similarity is structural -- shared audiences, overlapping features,
        matching source and deployment model -- so it needs no prose and creates
        no new URLs (spec 26 internal linking, spec 39).
        """
        scored: list[tuple[float, str, Client]] = []
        for other in self.listed:
            if other.slug == client.slug:
                continue
            shared_audiences = len(set(client.audiences) & set(other.audiences))
            shared_features = sum(
                1 for feature in self.taxonomy.core_features if client.has_feature(feature.id) and other.has_feature(feature.id)
            )
            weight = shared_audiences * 3.0
            weight += shared_features * 0.5
            if client.source_model is other.source_model:
                weight += 1.0
            if client.deployment is other.deployment:
                weight += 1.0
            if weight > 0:
                # Name is the tiebreak so the ordering is stable across builds.
                scored.append((weight, other.name.lower(), other))
        scored.sort(key=lambda row: (-row[0], row[1]))
        return tuple(row[2] for row in scored[:limit])


def load_site(root: Path, today: date | None = None) -> Site:
    """Load, validate, score, and join everything. No network access.

    `today` defaults to the observation timestamp rather than the wall clock, so
    a rebuild of an old commit produces the same maintenance ages -- and
    therefore the same scores -- as the original build (spec 44).
    """
    report = ValidationReport()

    taxonomy = load_taxonomy(root, report)
    validate_taxonomy(taxonomy, report)

    clients = load_clients(root, taxonomy, report)

    observations = load_observations(root)
    updated_at = next((obs.updated_at for obs in observations.values() if obs.updated_at), None)

    if today is None:
        today = _reference_date(updated_at)

    health = derive_all(clients, observations, today)
    scores = score_all(clients, taxonomy, {slug: result.status for slug, result in health.items()})
    prose = {client.slug: load_prose(root, client.slug, report) for client in clients}

    return Site(
        root=root,
        taxonomy=taxonomy,
        clients=clients,
        observations=observations,
        health=health,
        scores=scores,
        prose=prose,
        report=report,
        observations_updated_at=updated_at,
    )


def _reference_date(updated_at: str | None) -> date:
    """The date maintenance ages are measured against.

    Pinning to the observation timestamp keeps builds reproducible. With no
    observations, the choice does not matter: every client reads as UNKNOWN.
    """
    if updated_at:
        try:
            return datetime.fromisoformat(updated_at.replace("Z", "+00:00")).date()
        except ValueError:
            pass
    return date(1970, 1, 1)


def unpublished_reason(client: Client) -> str | None:
    """Why a record is absent from the directory, for the validate report."""
    if client.lifecycle is Lifecycle.CANDIDATE:
        return "candidate: review not finished"
    if client.lifecycle is Lifecycle.EXCLUDED:
        return "excluded: deliberately out of scope"
    return None
