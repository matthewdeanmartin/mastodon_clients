"""Deterministic star ratings (spec 17).

Every point in this module is traceable to a structured fact. Nothing here reads
prose, and no LLM contributes to a rating (invariant 4). Given the same commit,
two runs produce identical scores (spec 44).

`describe_components()` is what `/methodology/` renders, so the published
explanation of the formula cannot drift from the formula itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from mawkingbird.models import Client, Deployment, FeatureValue, Health, SourceModel
from mawkingbird.taxonomy import ACCESSIBILITY_FEATURE_IDS, Taxonomy

# Points available per component. They sum to 100.
FEATURE_BREADTH_MAX = 40
MAINTENANCE_MAX = 25
DEPLOYMENT_DOCS_MAX = 15
SUPPORT_MAX = 10
ACCESSIBILITY_MAX = 10

TOTAL_MAX = FEATURE_BREADTH_MAX + MAINTENANCE_MAX + DEPLOYMENT_DOCS_MAX + SUPPORT_MAX + ACCESSIBILITY_MAX

# Maintenance points by derived health status. `UNKNOWN` scores as low as
# `possibly-unmaintained` rather than zero: absent evidence is not evidence of
# abandonment (invariant 5), but it is also not evidence of health.
_MAINTENANCE_POINTS: dict[Health, int] = {
    Health.ACTIVELY_MAINTAINED: 25,
    Health.MAINTAINED: 20,
    Health.LOW_ACTIVITY: 12,
    Health.POSSIBLY_UNMAINTAINED: 6,
    Health.UNMAINTAINED: 0,
    Health.DISCONTINUED: 0,
    Health.UNKNOWN: 6,
}


@dataclass(frozen=True, slots=True)
class ComponentScore:
    """One scored component, with enough detail to show the reader the working."""

    id: str
    label: str
    points: float
    maximum: int
    detail: str

    @property
    def fraction(self) -> float:
        return self.points / self.maximum if self.maximum else 0.0


@dataclass(frozen=True, slots=True)
class Score:
    """A client's complete rating."""

    slug: str
    components: tuple[ComponentScore, ...]
    # Count of core features whose value is `unknown`. Surfaced separately so a
    # page can say "rated on incomplete information" rather than implying the
    # client lacks those features.
    unknown_features: int

    @property
    def points(self) -> float:
        return sum(component.points for component in self.components)

    @property
    def stars(self) -> float:
        """Points converted to a 0-5 scale in half-star steps.

        Half-star granularity is deliberate: finer resolution would imply a
        precision the inputs do not support.
        """
        raw = Decimal(self.points) / Decimal(TOTAL_MAX) * Decimal(5)
        halves = (raw * 2).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return float(halves) / 2

    @property
    def stars_label(self) -> str:
        stars = self.stars
        whole = int(stars)
        half = stars - whole
        return "★" * whole + ("½" if half else "") + "☆" * (5 - whole - (1 if half else 0))

    def component(self, component_id: str) -> ComponentScore | None:
        for component in self.components:
            if component.id == component_id:
                return component
        return None


def score_client(client: Client, taxonomy: Taxonomy, health: Health) -> Score:
    """Score one client. Pure: same inputs, same output, no I/O."""
    breadth, unknown = _feature_breadth(client, taxonomy)
    components = (
        breadth,
        _maintenance(health),
        _deployment_and_docs(client),
        _support(client),
        _accessibility(client, taxonomy),
    )
    return Score(slug=client.slug, components=components, unknown_features=unknown)


def _feature_breadth(client: Client, taxonomy: Taxonomy) -> tuple[ComponentScore, int]:
    """Fraction of core features supported, scaled to FEATURE_BREADTH_MAX.

    `not-applicable` leaves the denominator, because penalising a client for a
    feature that cannot apply to it would be measuring the wrong thing. `unknown`
    stays in the denominator and earns nothing -- missing information lowers the
    score, and the methodology says so.
    """
    core = taxonomy.core_features
    counted = 0
    earned = 0.0
    unknown = 0
    for feature in core:
        value = client.feature(feature.id)
        if value is FeatureValue.NOT_APPLICABLE:
            continue
        counted += 1
        earned += value.credit
        if value is FeatureValue.UNKNOWN:
            unknown += 1

    points = (earned / counted) * FEATURE_BREADTH_MAX if counted else 0.0
    detail = f"{earned:g} of {counted} core features"
    if unknown:
        detail += f" ({unknown} unknown)"
    return (
        ComponentScore(
            id="feature_breadth",
            label="Breadth of core features",
            points=round(points, 2),
            maximum=FEATURE_BREADTH_MAX,
            detail=detail,
        ),
        unknown,
    )


def _maintenance(health: Health) -> ComponentScore:
    """Points from the derived health status only -- never from a raw signal."""
    return ComponentScore(
        id="maintenance",
        label="Maintenance signals",
        points=float(_MAINTENANCE_POINTS[health]),
        maximum=MAINTENANCE_MAX,
        detail=health.label,
    )


def _deployment_and_docs(client: Client) -> ComponentScore:
    """Whether a prospective user can find out how to obtain and run the client."""
    earned = 0
    reasons: list[str] = []

    if client.link_url("documentation"):
        earned += 6
        reasons.append("documentation")
    if client.link_url("source"):
        earned += 4
        reasons.append("source available")
    if client.deployment is not Deployment.UNKNOWN:
        earned += 3
        reasons.append("deployment model recorded")
    # A self-hostable client without documentation is materially harder to use
    # than a hosted one without documentation, so the pairing is worth a point.
    if client.deployment in (
        Deployment.SELF_HOSTABLE,
        Deployment.HOSTED_AND_SELF_HOSTABLE,
    ) and client.link_url("documentation"):
        earned += 2
        reasons.append("self-host instructions")

    return ComponentScore(
        id="deployment_docs",
        label="Deployment and documentation",
        points=float(earned),
        maximum=DEPLOYMENT_DOCS_MAX,
        detail=", ".join(reasons) if reasons else "none recorded",
    )


def _support(client: Client) -> ComponentScore:
    """Whether a user with a problem has somewhere to take it."""
    earned = 0
    reasons: list[str] = []
    for link_type, points, label in (
        ("issues", 4, "issue tracker"),
        ("support", 3, "support channel"),
        ("community", 2, "community space"),
        ("changelog", 1, "changelog"),
    ):
        if client.link_url(link_type):
            earned += points
            reasons.append(label)
    return ComponentScore(
        id="support",
        label="Support and resources",
        points=float(earned),
        maximum=SUPPORT_MAX,
        detail=", ".join(reasons) if reasons else "none recorded",
    )


def _accessibility(client: Client, taxonomy: Taxonomy) -> ComponentScore:
    """Accessibility-related capabilities, scaled to ACCESSIBILITY_MAX.

    Only features that exist in the taxonomy count, so the denominator tracks
    the vocabulary rather than a stale hard-coded list.
    """
    ids = sorted(ACCESSIBILITY_FEATURE_IDS & taxonomy.feature_ids)
    if not ids:
        return ComponentScore(
            id="accessibility",
            label="Accessibility",
            points=0.0,
            maximum=ACCESSIBILITY_MAX,
            detail="no accessibility features in taxonomy",
        )

    earned = sum(client.feature(feature_id).credit for feature_id in ids)
    points = (earned / len(ids)) * ACCESSIBILITY_MAX
    return ComponentScore(
        id="accessibility",
        label="Accessibility",
        points=round(points, 2),
        maximum=ACCESSIBILITY_MAX,
        detail=f"{earned:g} of {len(ids)} accessibility features",
    )


def score_all(clients: tuple[Client, ...], taxonomy: Taxonomy, health: dict[str, Health]) -> dict[str, Score]:
    """Score every client. Unhealthy-signal absence defaults to UNKNOWN, not zero."""
    return {client.slug: score_client(client, taxonomy, health.get(client.slug, Health.UNKNOWN)) for client in clients}


@dataclass(frozen=True, slots=True)
class ComponentDescription:
    """The public description of one rating component.

    A typed record rather than a dict, so the methodology page and the tests
    read `.maximum` instead of casting an `object` at every use site.
    """

    id: str
    label: str
    maximum: int
    description: str


def describe_components() -> tuple[ComponentDescription, ...]:
    """The public description of the formula, rendered on `/methodology/`.

    Kept beside the implementation so the published explanation cannot drift
    from what the code actually does (spec 17: the algorithm is documented
    publicly).
    """
    return (
        ComponentDescription(
            id="feature_breadth",
            label="Breadth of core features",
            maximum=FEATURE_BREADTH_MAX,
            description=(
                "The share of core features the client supports. A feature marked partial counts as half. "
                "A feature marked not-applicable is removed from the denominator rather than counted against "
                "the client. A feature we have not established counts as unknown: it earns nothing, so missing "
                "information does lower this score. The number of unknowns is published alongside the rating "
                "so an incompletely researched client is not mistaken for a poor one."
            ),
        ),
        ComponentDescription(
            id="maintenance",
            label="Maintenance signals",
            maximum=MAINTENANCE_MAX,
            description=(
                "Derived from the synthesised maintenance status, which is itself computed from several "
                "independent signals. No single signal can move a client to unmaintained or discontinued. "
                "Where signals are absent, the status is unknown, which scores the same as possibly "
                "unmaintained -- absent evidence is not evidence of abandonment, but neither is it evidence "
                "of health."
            ),
        ),
        ComponentDescription(
            id="deployment_docs",
            label="Deployment and documentation",
            maximum=DEPLOYMENT_DOCS_MAX,
            description=(
                "Whether a prospective user can find out how to obtain and run the client: documentation (6), "
                "available source (4), a recorded deployment model (3), and documentation for a client that "
                "must be self-hosted (2)."
            ),
        ),
        ComponentDescription(
            id="support",
            label="Support and resources",
            maximum=SUPPORT_MAX,
            description=(
                "Whether a user with a problem has somewhere to take it: an issue tracker (4), a support "
                "channel (3), a community space (2), and a changelog (1)."
            ),
        ),
        ComponentDescription(
            id="accessibility",
            label="Accessibility",
            maximum=ACCESSIBILITY_MAX,
            description=(
                "The share of accessibility-related capabilities the client offers: keyboard navigation, "
                "deliberate accessibility work, content warnings, reduced-motion support, and a responsive "
                "layout."
            ),
        ),
    )


def source_model_label(source_model: SourceModel) -> str:
    """Human label for a source model, used by templates and JSON alike."""
    return {
        SourceModel.OPEN_SOURCE: "Open source",
        SourceModel.CLOSED_SOURCE: "Closed source",
        SourceModel.HYBRID: "Hybrid",
        SourceModel.UNKNOWN: "Unknown",
    }[source_model]
