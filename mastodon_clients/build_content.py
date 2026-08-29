"""Assembly of Pelican-ready content from the data layer (spec 22, 46).

This is the join step: structured TOML, machine observations, generated prose,
and human overrides go in; Markdown with complete front matter comes out.
Templates then concentrate on presentation and do no data processing.

Two properties matter here. It performs no network access, and it is
deterministic -- sorted keys, stable ordering, dates taken from data rather than
the clock -- so two builds of one commit produce identical output (spec 44).
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mastodon_clients.models import CHECKABLE_LINK_TYPES, Client, Deployment, ServerDependency, SourceModel
from mastodon_clients.overrides import SECTION_LABELS, SECTIONS
from mastodon_clients.repository import Site
from mastodon_clients.scoring import describe_components

# Where the generated Pelican content tree lives. Wiped and rewritten on every
# build, so nothing hand-edited may be placed here -- hand-written pages live in
# `content/pages/`, which is never touched.
GENERATED_ROOT = Path("content") / "_generated"


@dataclass(frozen=True, slots=True)
class PageContext:
    """Everything a template needs about one client, precomputed."""

    client: Client
    payload: dict[str, Any]


def build_content(site: Site) -> int:
    """Write the whole generated content tree. Returns the file count."""
    target = site.root / GENERATED_ROOT
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    written = 0
    written += _write_directory(site, target)
    written += _write_clients(site, target)
    written += _write_audiences(site, target)
    written += _write_features(site, target)
    written += _write_facets(site, target)
    written += _write_comparisons(site, target)
    written += _write_methodology(site, target)
    written += _write_json(site)
    return written


# --- serialisation ---------------------------------------------------------


def client_payload(site: Site, client: Client) -> dict[str, Any]:
    """The canonical serialisation of a client.

    Used by the HTML templates, the JSON endpoints, and the comparison tables
    alike, so all three necessarily agree (spec 27: no separate hand-maintained
    HTML facts and JSON facts).
    """
    score = site.scores[client.slug]
    health = site.health.get(client.slug)
    prose = site.prose.get(client.slug)
    observations = site.observations.get(client.slug)

    features: list[dict[str, Any]] = []
    for feature in site.taxonomy.features:
        value = client.feature(feature.id)
        features.append(
            {
                "id": feature.id,
                "label": feature.label,
                "description": feature.description,
                "core": feature.core,
                "url": feature.url if feature.page else None,
                "value": value.value,
                "value_label": value.label,
            }
        )

    links: list[dict[str, Any]] = []
    for link in client.links:
        observation = observations.get(f"{link.type}_http") if observations else None
        links.append(
            {
                "type": link.type,
                "url": link.url,
                "label": link.display_label,
                # The editorially recorded URL is never replaced by an
                # observation; the observed state sits beside it (spec 32).
                "last_check": _describe_check(observation),
                "checkable": link.check and link.type in CHECKABLE_LINK_TYPES,
            }
        )

    prose_sections = []
    if prose is not None:
        for section_id in SECTIONS:
            text = prose.section(section_id)
            if text:
                prose_sections.append(
                    {
                        "id": section_id,
                        "label": SECTION_LABELS[section_id],
                        "text": text,
                        "overridden": prose.is_overridden(section_id),
                    }
                )

    return {
        "slug": client.slug,
        "name": client.name,
        "summary": client.summary,
        "url": client.url,
        "status": client.lifecycle.value,
        "source_model": client.source_model.value,
        "source_model_label": _SOURCE_LABELS[client.source_model],
        "license": client.licence,
        "deployment": client.deployment.value,
        "deployment_label": _DEPLOYMENT_LABELS[client.deployment],
        "server_dependency": client.server_dependency.value,
        "server_dependency_label": _DEPENDENCY_LABELS[client.server_dependency],
        "standalone": client.server_dependency is ServerDependency.INDEPENDENT,
        "funding_model": [funding.value for funding in client.funding_model],
        "funding_labels": [funding.value.replace("-", " ").capitalize() for funding in client.funding_model],
        "audiences": [
            {"id": audience_id, "label": _audience_label(site, audience_id), "url": f"/for/{audience_id}/"}
            for audience_id in client.audiences
        ],
        "features": features,
        "links": links,
        "screenshots": [
            {
                "path": shot.path,
                "caption": shot.caption,
                "source_url": shot.source_url,
                "captured_at": shot.captured_at.isoformat() if shot.captured_at else None,
            }
            for shot in client.screenshots
        ],
        "rating": {
            "stars": score.stars,
            "stars_label": score.stars_label,
            "points": round(score.points, 1),
            "unknown_features": score.unknown_features,
            "components": [
                {
                    "id": component.id,
                    "label": component.label,
                    "points": component.points,
                    "maximum": component.maximum,
                    "detail": component.detail,
                }
                for component in score.components
            ],
        },
        "health": {
            "status": health.status.value if health else "unknown",
            "label": health.status.label if health else "Unknown",
            "reasons": list(health.reasons) if health else [],
            "warnings": [warning.message for warning in health.warnings] if health else [],
        },
        "observations": _observation_rows(site, client),
        "reviewed_at": client.reviewed_at.isoformat(),
        "observations_updated_at": site.observations_updated_at,
        "discontinued_at": client.discontinued_at.isoformat() if client.discontinued_at else None,
        "discontinued_evidence": client.discontinued_evidence,
        "successors": [
            {"slug": slug, "name": _client_name(site, slug), "url": f"/clients/{slug}/"} for slug in client.successors
        ],
        # The question almost every visitor actually has. Surfaced as its own
        # field so a template does not have to translate a deployment model into
        # "is there a URL I can click".
        "public_instance": client.public_instance,
        "is_fork": client.is_fork,
        "fork_note": client.fork_note,
        "fork_of": (
            {
                "slug": client.fork_of,
                "name": _client_name(site, client.fork_of),
                "url": f"/clients/{client.fork_of}/",
            }
            if client.fork_of
            else None
        ),
        "forks": [
            {
                "slug": fork.slug,
                "name": fork.name,
                "url": fork.url,
                "summary": fork.summary,
                "note": fork.fork_note,
                "status": site.status_of(fork.slug).value,
                "status_label": site.status_of(fork.slug).label,
                "stars": site.scores[fork.slug].stars,
                "license": fork.licence,
                "public_instance": fork.public_instance,
            }
            for fork in site.forks_of(client.slug)
        ],
        "family_status": site.family_status(client).value,
        "family_status_label": site.family_status(client).label,
        "prose": prose_sections,
        "related": [
            {"slug": other.slug, "name": other.name, "url": other.url, "summary": other.summary}
            for other in site.related(client)
        ],
    }


def _describe_check(observation: object) -> dict[str, Any] | None:
    """Render an observation as a "last check" note beside its editorial link."""
    if observation is None:
        return None
    obs: Any = observation
    status = obs.value.get("status") if obs.value else None
    return {
        "ok": obs.ok,
        "status": status,
        "at": obs.observed_at,
        "error": obs.error,
        "summary": (f"{status}" if obs.ok and status else (obs.error or "unreachable")),
    }


def _observation_rows(site: Site, client: Client) -> list[dict[str, Any]]:
    """Every raw signal, sorted, so a reader can see why a status was assigned."""
    observations = site.observations.get(client.slug)
    if observations is None:
        return []
    rows = []
    for signal in sorted(observations.by_signal):
        obs = observations.by_signal[signal]
        rows.append(
            {
                "signal": signal,
                "label": signal.replace("_", " ").capitalize(),
                "ok": obs.ok,
                "observed_at": obs.observed_at,
                "source": obs.source,
                "value": obs.value,
                "error": obs.error,
            }
        )
    return rows


_SOURCE_LABELS = {
    SourceModel.OPEN_SOURCE: "Open source",
    SourceModel.CLOSED_SOURCE: "Closed source",
    SourceModel.HYBRID: "Hybrid",
    SourceModel.UNKNOWN: "Unknown",
}

_DEPLOYMENT_LABELS = {
    Deployment.HOSTED: "Hosted",
    Deployment.SELF_HOSTABLE: "Self-hostable",
    Deployment.HOSTED_AND_SELF_HOSTABLE: "Hosted or self-hostable",
    Deployment.BUNDLED_WITH_SERVER: "Bundled with a server",
    Deployment.UNKNOWN: "Unknown",
}

_DEPENDENCY_LABELS = {
    ServerDependency.INDEPENDENT: "Works with any server",
    ServerDependency.REQUIRES_SERVER_DEPLOYMENT: "Requires deploying a server",
    ServerDependency.UNKNOWN: "Unknown",
}


def _audience_label(site: Site, audience_id: str) -> str:
    audience = site.taxonomy.audience(audience_id)
    return audience.label if audience else audience_id


def _client_name(site: Site, slug: str) -> str:
    client = site.client(slug)
    return client.name if client else slug


# --- page writers ----------------------------------------------------------


def _front_matter(fields: dict[str, str]) -> list[str]:
    """Pelican Markdown metadata lines, in a fixed order for deterministic output."""
    order = ("Title", "Slug", "URL", "Save_as", "Template", "Description", "Status", "Date")
    lines = [f"{key}: {fields[key]}" for key in order if key in fields]
    lines += [f"{key}: {fields[key]}" for key in sorted(set(fields) - set(order))]
    return lines


def _write(path: Path, front: dict[str, str], data: dict[str, Any]) -> None:
    """Write one content file.

    The payload rides in a `Data` metadata field as compact JSON on a single
    line. Pelican's Markdown meta extension ends the metadata block at the first
    blank line, so `Data` has to sit inside that block with no blank line before
    it. Templates parse it with the `data` filter and then render; every join
    already happened in Python (spec 46).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = _front_matter(front)
    lines.append("Data: " + json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    path.write_text("\n".join(lines) + "\n\n", encoding="utf-8")


def _write_directory(site: Site, target: Path) -> int:
    clients = [client_payload(site, client) for client in site.listed]
    _write(
        target / "clients-index.md",
        {
            "Title": "Mastodon web client directory",
            "URL": "clients/",
            "Save_as": "clients/index.html",
            "Template": "directory",
            "Description": (
                f"Every Mastodon-compatible web client reviewed on Mawkingbird: {len(clients)} clients, "
                "with features, licensing, deployment model, and maintenance signals."
            ),
        },
        {
            "clients": clients,
            "features": [
                {"id": f.id, "label": f.label, "core": f.core, "url": f.url if f.page else None}
                for f in site.taxonomy.features
            ],
            "audiences": [{"id": a.id, "label": a.label, "url": a.url} for a in site.taxonomy.audiences],
        },
    )
    return 1


def _write_clients(site: Site, target: Path) -> int:
    written = 0
    # `with_pages`, not `listed`: a fork keeps its own page even though it does
    # not occupy a directory row.
    for client in site.with_pages:
        payload = client_payload(site, client)
        # A discontinued client keeps its canonical URL and gets a historical
        # page rather than disappearing (spec 5.7, invariant 9).
        template = "historical" if client.lifecycle.historical else "client"
        _write(
            target / "clients" / f"{client.slug}.md",
            {
                "Title": client.name,
                "URL": f"clients/{client.slug}/",
                "Save_as": f"clients/{client.slug}/index.html",
                "Template": template,
                "Description": client.summary[:300],
            },
            payload,
        )
        written += 1
    return written


def _write_audiences(site: Site, target: Path) -> int:
    written = 0
    for audience in site.taxonomy.audiences:
        matching = site.by_audience(audience.id)
        # Order by how well each client meets that audience's stated criteria,
        # then by rating, then by name -- deterministic and explainable.
        ranked = sorted(
            matching,
            key=lambda c: (
                -sum(1 for feature_id in audience.criteria if c.has_feature(feature_id)),
                -site.scores[c.slug].points,
                c.name.lower(),
            ),
        )
        _write(
            target / "for" / f"{audience.id}.md",
            {
                "Title": audience.label,
                "URL": f"for/{audience.id}/",
                "Save_as": f"for/{audience.id}/index.html",
                "Template": "audience",
                "Description": f"Mastodon web clients suited to {audience.label.lower()}.",
            },
            {
                "audience": {"id": audience.id, "label": audience.label, "intro": audience.intro},
                "criteria": [
                    {"id": fid, "label": _feature_label(site, fid), "url": _feature_url(site, fid)}
                    for fid in audience.criteria
                ],
                "clients": [client_payload(site, client) for client in ranked],
            },
        )
        written += 1
    return written


def _write_features(site: Site, target: Path) -> int:
    written = 0
    for feature in site.taxonomy.page_features:
        matching = site.by_feature(feature.id)
        _write(
            target / "features" / f"{feature.id.replace('_', '-')}.md",
            {
                "Title": feature.label,
                "URL": feature.url.strip("/") + "/",
                "Save_as": feature.url.strip("/") + "/index.html",
                "Template": "feature",
                "Description": f"Mastodon web clients that support {feature.label.lower()}. {feature.description}"[:300],
            },
            {
                "feature": {"id": feature.id, "label": feature.label, "description": feature.description},
                "clients": [client_payload(site, client) for client in matching],
                "without": [
                    {"slug": c.slug, "name": c.name, "url": c.url, "value": c.feature(feature.id).label}
                    for c in site.listed
                    if not c.has_feature(feature.id)
                ],
            },
        )
        written += 1
    return written


def _write_facets(site: Site, target: Path) -> int:
    """The three curated source/deployment facets of spec 5.5.

    Only these three exist. Arbitrary metadata combinations stay user-interface
    state rather than becoming crawlable URLs (spec 30).
    """
    facets = (
        (
            "open-source",
            "Open-source Mastodon web clients",
            "Clients whose source is published under a licence that permits inspection and modification. "
            "Source availability and licence are recorded as separate facts: a client can be open source "
            "under several different licences, and a published repository is not by itself a licence grant.",
            site.by_source_model(SourceModel.OPEN_SOURCE),
        ),
        (
            "hosted",
            "Hosted Mastodon web clients",
            "Clients you can use immediately at a URL, without deploying anything. Some of these can also "
            "be self-hosted; the individual reviews say which.",
            site.by_deployment(Deployment.HOSTED, Deployment.HOSTED_AND_SELF_HOSTABLE),
        ),
        (
            "standalone",
            "Standalone Mastodon web clients",
            "Clients that work with any Mastodon-compatible server, rather than requiring you to deploy a "
            "server of your own. This is a different question from whether the client can be self-hosted: "
            "an alternative frontend may be self-hostable and still need its own backend.",
            site.standalone(),
        ),
    )
    for slug, title, intro, clients in facets:
        _write(
            target / "facets" / f"{slug}.md",
            {
                "Title": title,
                "URL": f"{slug}/",
                "Save_as": f"{slug}/index.html",
                "Template": "facet",
                "Description": intro[:300],
            },
            {"intro": intro, "clients": [client_payload(site, client) for client in clients]},
        )
    return len(facets)


def _write_comparisons(site: Site, target: Path) -> int:
    """Allow-listed comparison pages only (spec 5.6, invariant 8).

    Everything on the page is derived from structured data. No pairwise prose is
    authored or generated, and the quadratic set is never produced.
    """
    written = 0
    for comparison in site.taxonomy.comparisons:
        left = site.client(comparison.left)
        right = site.client(comparison.right)
        if left is None or right is None:
            continue
        rows = []
        for feature in site.taxonomy.features:
            left_value, right_value = left.feature(feature.id), right.feature(feature.id)
            rows.append(
                {
                    "id": feature.id,
                    "label": feature.label,
                    "core": feature.core,
                    "left": left_value.label,
                    "right": right_value.label,
                    "differs": left_value is not right_value,
                }
            )
        _write(
            target / "compare" / f"{left.slug}-{right.slug}.md",
            {
                "Title": f"{left.name} compared with {right.name}",
                "URL": f"compare/{left.slug}/{right.slug}/",
                "Save_as": f"compare/{left.slug}/{right.slug}/index.html",
                "Template": "comparison",
                "Description": (
                    f"A side-by-side comparison of {left.name} and {right.name}, derived from structured "
                    "metadata: features, licensing, deployment model, funding, and maintenance signals."
                ),
            },
            {
                "left": client_payload(site, left),
                "right": client_payload(site, right),
                "features": rows,
            },
        )
        written += 1
    return written


def _write_methodology(site: Site, target: Path) -> int:
    """The scoring formula, rendered from the code that implements it.

    Publishing a hand-written description would let the published explanation
    drift from the actual formula, which spec 17 requires be documented.
    """
    _write(
        target / "methodology-scoring.md",
        {
            "Title": "How ratings are calculated",
            "URL": "methodology/scoring/",
            "Save_as": "methodology/scoring/index.html",
            "Template": "scoring",
            "Description": "The exact formula behind Mawkingbird's star ratings, generated from the code that computes them.",
        },
        {
            "components": [
                {
                    "id": component.id,
                    "label": component.label,
                    "maximum": component.maximum,
                    "description": component.description,
                }
                for component in describe_components()
            ],
            "total": sum(component.maximum for component in describe_components()),
            "features": [
                {"id": f.id, "label": f.label, "core": f.core, "description": f.description}
                for f in site.taxonomy.features
            ],
        },
    )
    return 1


def _write_json(site: Site) -> int:
    """Machine-readable feeds (spec 27).

    Written into `content/extra/` and copied verbatim by Pelican, so they come
    from the same canonical payload the HTML uses.
    """
    extra = site.root / "content" / "extra"
    extra.mkdir(parents=True, exist_ok=True)

    clients = [client_payload(site, client) for client in site.with_pages]
    _dump(extra / "clients.json", {"clients": clients, "generated_from": "data/clients/*.toml"})

    per_client = extra / "clients"
    if per_client.exists():
        shutil.rmtree(per_client)
    per_client.mkdir(parents=True)
    for payload in clients:
        _dump(per_client / f"{payload['slug']}.json", payload)

    _dump(
        extra / "features.json",
        {
            "features": [
                {
                    "id": f.id,
                    "label": f.label,
                    "description": f.description,
                    "core": f.core,
                    "url": f.url if f.page else None,
                }
                for f in site.taxonomy.features
            ]
        },
    )
    return len(clients) + 2


def _dump(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _feature_label(site: Site, feature_id: str) -> str:
    feature = site.taxonomy.feature(feature_id)
    return feature.label if feature else feature_id


def _feature_url(site: Site, feature_id: str) -> str | None:
    feature = site.taxonomy.feature(feature_id)
    return feature.url if feature and feature.page else None
