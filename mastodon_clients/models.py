"""Domain model for the client directory.

These types are the canonical in-memory shape of a client record. Everything the
site renders -- HTML, JSON-LD, `/clients.json`, comparison tables -- is derived
from them, so there is never a second hand-maintained set of facts (spec 27, 47).

Enums are closed on purpose. An unrecognised status or deployment model is a
validation error, not a value that silently reaches a template (spec 24).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


class Lifecycle(StrEnum):
    """Editorial lifecycle (spec 33).

    Set by a human, never by a machine observation. `candidate` lets a record
    exist before its review is finished; `excluded` records a deliberate
    out-of-scope decision without publishing a review.
    """

    CANDIDATE = "candidate"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"
    EXCLUDED = "excluded"

    @property
    def published(self) -> bool:
        """Whether this record gets an ordinary published review page."""
        return self in (Lifecycle.ACTIVE, Lifecycle.INACTIVE)

    @property
    def historical(self) -> bool:
        """Whether this record gets a minimal historical page (spec 5.7)."""
        return self is Lifecycle.DISCONTINUED


class SourceModel(StrEnum):
    """Source availability (spec 11). Kept separate from the licence field."""

    OPEN_SOURCE = "open-source"
    CLOSED_SOURCE = "closed-source"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"


class Deployment(StrEnum):
    """How the client is obtained and run (spec 12)."""

    HOSTED = "hosted"
    SELF_HOSTABLE = "self-hostable"
    HOSTED_AND_SELF_HOSTABLE = "hosted-and-self-hostable"
    BUNDLED_WITH_SERVER = "bundled-with-server"
    UNKNOWN = "unknown"


class ServerDependency(StrEnum):
    """Whether the client can run without deploying a Mastodon-compatible server.

    Distinct from `Deployment`: a self-hostable frontend that still requires its
    own backend is a materially different proposition from one that talks to any
    instance (spec 12).
    """

    INDEPENDENT = "independent"
    REQUIRES_SERVER_DEPLOYMENT = "requires-server-deployment"
    UNKNOWN = "unknown"


class Funding(StrEnum):
    """Funding model (spec 13). A client may carry several."""

    COMMERCIAL = "commercial"
    FREEMIUM = "freemium"
    DONATIONS = "donations"
    SPONSORSHIP = "sponsorship"
    GRANTS = "grants"
    VOLUNTEER = "volunteer"
    BUNDLED_WITH_COMMERCIAL_PRODUCT = "bundled-with-commercial-product"
    UNKNOWN = "unknown"


class Health(StrEnum):
    """Derived maintenance status (spec 14).

    Produced only by `mastodon_clients.health` from several observations. No single
    signal may reach `UNMAINTAINED` or `DISCONTINUED` (invariant 5).
    """

    ACTIVELY_MAINTAINED = "actively-maintained"
    MAINTAINED = "maintained"
    LOW_ACTIVITY = "low-activity"
    POSSIBLY_UNMAINTAINED = "possibly-unmaintained"
    UNMAINTAINED = "unmaintained"
    DISCONTINUED = "discontinued"
    UNKNOWN = "unknown"

    @property
    def label(self) -> str:
        return self.value.replace("-", " ").capitalize()


class FeatureValue(StrEnum):
    """A feature's state for one client (spec 10).

    Booleans in TOML normalise to YES/NO. The wider vocabulary exists from the
    start so adding a `partial` to a record later is a data edit, not a schema
    migration.
    """

    YES = "yes"
    NO = "no"
    PARTIAL = "partial"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not-applicable"

    @classmethod
    def parse(cls, raw: object) -> FeatureValue:
        """Normalise a TOML scalar. Raises ValueError for anything unrecognised."""
        if isinstance(raw, bool):
            return cls.YES if raw else cls.NO
        if isinstance(raw, str):
            return cls(raw.strip().lower())
        raise ValueError(f"expected a boolean or string, got {type(raw).__name__}")

    @property
    def credit(self) -> float:
        """Fraction of a feature point this value earns (spec 17).

        `partial` earns half. `unknown` earns nothing and is counted separately
        so the methodology can say plainly that missing information lowers a
        score. `not-applicable` is excluded from the denominator by the caller.
        """
        return {
            FeatureValue.YES: 1.0,
            FeatureValue.PARTIAL: 0.5,
            FeatureValue.NO: 0.0,
            FeatureValue.UNKNOWN: 0.0,
            FeatureValue.NOT_APPLICABLE: 0.0,
        }[self]

    @property
    def label(self) -> str:
        return {
            FeatureValue.YES: "Yes",
            FeatureValue.NO: "No",
            FeatureValue.PARTIAL: "Partial",
            FeatureValue.UNKNOWN: "Unknown",
            FeatureValue.NOT_APPLICABLE: "N/A",
        }[self]


# Link types recognised by the schema (spec 9). Unknown types fail validation
# rather than passing through, so a typo cannot quietly produce an unrendered link.
#
# `homepage` and `hosted` are different things and must not be conflated. A
# homepage is where the project describes itself -- a project page, a docs site,
# or the repository README. `hosted` is a URL where the client actually runs.
# Many projects have only one of the two, and recording a running deployment as
# a homepage overstates what the project publishes about itself.
LINK_TYPES: tuple[str, ...] = (
    "homepage",
    "hosted",
    "canary",
    "documentation",
    "source",
    "issues",
    "releases",
    "changelog",
    "funding",
    "support",
    "privacy",
    "terms",
    "community",
)

# Link types worth an automated reachability check by default (spec 32).
CHECKABLE_LINK_TYPES: frozenset[str] = frozenset({
    "homepage",
    "hosted",
    "canary",
    "documentation",
    "source",
    "issues",
    "releases",
})


@dataclass(frozen=True, slots=True)
class Link:
    """One typed product link.

    Links are first-class data, not prose (spec 9). A client may have several of
    the same type -- two source repositories, a hosted app plus a canary -- so
    the internal representation is always a list even when the TOML used the
    single-value `[links]` table form.
    """

    type: str
    url: str
    label: str | None = None
    check: bool = True

    @property
    def display_label(self) -> str:
        return self.label or self.type.replace("-", " ").capitalize()


@dataclass(frozen=True, slots=True)
class Screenshot:
    """A product screenshot (spec 31).

    Present in the model from the start so imagery does not require a schema
    change later; no seed record is expected to use it.
    """

    path: str
    caption: str | None = None
    source_url: str | None = None
    captured_at: date | None = None


@dataclass(frozen=True, slots=True)
class Prose:
    """Prose file locations for a client (spec 20).

    Generated and override prose live in separate trees so that regeneration can
    never overwrite human editorial authority (invariant 3).
    """

    generated_file: str | None = None
    override_file: str | None = None


@dataclass(frozen=True, slots=True)
class Client:
    """One reviewed client, as recorded in `data/clients/<slug>.toml`."""

    slug: str
    name: str
    summary: str
    lifecycle: Lifecycle
    source_model: SourceModel
    deployment: Deployment
    server_dependency: ServerDependency
    reviewed_at: date
    licence: str | None = None
    funding_model: tuple[Funding, ...] = ()
    audiences: tuple[str, ...] = ()
    features: dict[str, FeatureValue] = field(default_factory=dict)
    links: tuple[Link, ...] = ()
    screenshots: tuple[Screenshot, ...] = ()
    prose: Prose = field(default_factory=Prose)
    # Fork lineage. A fork names the family it belongs to, so the directory can
    # list one row per family instead of repeating near-identical clients --
    # Pinafore, Semaphore, and Enafore are one lineage, and listing them as three
    # peers tells a reader to "use Pinafore, or Pinafore, or Pinafore".
    #
    # Deliberately one level deep: a fork of a fork records the family root. The
    # alternative is a tree nobody wants to read, to answer a question ("which
    # of these should I use?") that a flat list of siblings answers better.
    fork_of: str | None = None
    fork_note: str | None = None
    # Discontinuation record (spec 5.7). Only meaningful for DISCONTINUED clients.
    discontinued_at: date | None = None
    discontinued_evidence: str | None = None
    successors: tuple[str, ...] = ()
    # Provenance of the record itself, not of any generated prose.
    source_file: str = ""

    @property
    def url(self) -> str:
        """Canonical site URL. Stable across lifecycle changes (invariant 9)."""
        return f"/clients/{self.slug}/"

    @property
    def is_fork(self) -> bool:
        """Whether this record belongs to another client's family."""
        return self.fork_of is not None

    @property
    def homepage(self) -> str | None:
        return self.link_url("homepage")

    @property
    def public_instance(self) -> str | None:
        """A URL a reader can simply open, or None.

        Distinct from `homepage`, which is where the project describes itself.
        This is the question almost every visitor actually has, so it gets its
        own accessor rather than being inferred from the deployment model.
        """
        return self.link_url("hosted")

    def link_url(self, link_type: str) -> str | None:
        """First URL of a given type, or None."""
        for link in self.links:
            if link.type == link_type:
                return link.url
        return None

    def links_of(self, link_type: str) -> tuple[Link, ...]:
        return tuple(link for link in self.links if link.type == link_type)

    def feature(self, feature_id: str) -> FeatureValue:
        """A feature's value, defaulting to UNKNOWN for anything unrecorded.

        Defaulting rather than raising matters: adding a feature to the taxonomy
        must not invalidate every existing client record.
        """
        return self.features.get(feature_id, FeatureValue.UNKNOWN)

    def has_feature(self, feature_id: str) -> bool:
        """Whether the client counts as offering the feature, for facet pages."""
        return self.feature(feature_id) in (FeatureValue.YES, FeatureValue.PARTIAL)


@dataclass(frozen=True, slots=True)
class Observation:
    """One machine-collected signal (spec 16).

    Observations inform status. They never overwrite editorial metadata, and
    never change `Client.lifecycle` (spec 33, 47).
    """

    client: str
    signal: str
    observed_at: str
    source: str
    ok: bool
    value: dict[str, object] = field(default_factory=dict)
    error: str | None = None
