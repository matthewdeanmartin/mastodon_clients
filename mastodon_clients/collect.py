"""Machine metadata collection (spec 15).

This is the only module in the package that touches the network, and nothing on
the build path imports it (invariant 1). It runs when a human types
`make refresh-metadata`; it is not scheduled, and it never runs during a Pelican
build.

Its output, `data/generated/observations.json`, is committed and reviewed like
any other change. That is what keeps builds reproducible: the site renders from
a file in git, not from whatever the internet said at build time (spec 44).

Nothing here writes to a client's TOML. Observations inform status; they never
overwrite editorial metadata (spec 47).
"""

from __future__ import annotations

import json
import re
import socket
import ssl
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from mastodon_clients.models import CHECKABLE_LINK_TYPES, Client, Observation
from mastodon_clients.repository import Site

OBSERVATIONS_PATH = Path("data") / "generated" / "observations.json"

# A descriptive agent string is a courtesy to the operators whose sites this
# checks: it tells them who is asking and where to complain.
USER_AGENT = (
    "MastodonClientsDirectoryBot/0.1 "
    "(+https://github.com/matthewdeanmartin/mastodon_clients; directory metadata check)"
)

_GITHUB_RE = re.compile(r"^https?://(?:www\.)?github\.com/([^/]+)/([^/#?]+)")
_GITLAB_RE = re.compile(r"^https?://(?:www\.)?gitlab\.com/(.+?)/?(?:$|[#?])")


@dataclass(slots=True)
class Collector:
    """Holds the HTTP client and accumulates observations."""

    timeout: float
    now: str
    observations: list[Observation]

    def record(
        self,
        client: str,
        signal: str,
        *,
        source: str,
        ok: bool,
        value: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        self.observations.append(
            Observation(
                client=client,
                signal=signal,
                observed_at=self.now,
                source=source,
                ok=ok,
                value=value or {},
                error=error,
            )
        )


def refresh_metadata(site: Site, only: str | None = None, timeout: float = 10.0) -> int:
    """Collect observations for every client, or one named client.

    Prints a human-readable diff against the previously committed file (spec 36)
    and any conditions worth attention (spec 38), then writes the new file.
    """
    try:
        import httpx
    except ImportError:
        print(
            "The collect extra is not installed. Run:\n  uv sync --extra collect\nor: make refresh-metadata",
            file=sys.stderr,
        )
        return 1

    targets = [c for c in site.clients if only is None or c.slug == only]
    if only and not targets:
        print(f"Unknown client {only!r}.", file=sys.stderr)
        return 1

    previous = _load_previous(site.root)
    collector = Collector(
        timeout=timeout,
        now=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        observations=[],
    )

    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as http:
        for client in targets:
            print(f"Collecting {client.slug}...")
            _collect_links(collector, http, client)
            _collect_hosts(collector, client)
            _collect_repository(collector, http, client)

    # A partial refresh must keep the observations it did not re-collect, or
    # `make refresh-metadata CLIENT=x` would silently blank every other client.
    merged = dict(previous)
    for observation in collector.observations:
        merged[(observation.client, observation.signal)] = observation

    _print_diff(previous, {(o.client, o.signal): o for o in collector.observations})
    _print_warnings(site, merged)
    _write(site.root, collector.now, merged)

    print(f"\nWrote {OBSERVATIONS_PATH} ({len(merged)} observations).")
    print("Review the diff and commit it. The site builds from the committed file.")
    return 0


# --- collectors ------------------------------------------------------------


def _collect_links(collector: Collector, http: Any, client: Client) -> None:
    """Reachability of each checkable editorial link (spec 32).

    A failure here is recorded as an observation. It never removes or rewrites
    the recorded URL: a temporary outage must not erase a fact.
    """
    for link in client.links:
        if not link.check or link.type not in CHECKABLE_LINK_TYPES:
            continue
        signal = f"{link.type}_http"
        try:
            # HEAD first: cheaper, and polite to the operators being checked.
            # Plenty of sites answer HEAD with 403 or 405, so fall back to GET.
            response = http.head(link.url)
            if response.status_code >= 400:
                response = http.get(link.url)
            collector.record(
                client.slug,
                signal,
                source="http",
                ok=response.status_code < 400,
                value={"status": response.status_code, "url": str(response.url)},
                error=None if response.status_code < 400 else f"HTTP {response.status_code}",
            )
        except Exception as exc:
            collector.record(client.slug, signal, source="http", ok=False, error=_describe(exc))


def _collect_hosts(collector: Collector, client: Client) -> None:
    """DNS resolution and TLS validity for each distinct host."""
    hosts: set[str] = set()
    for link in client.links:
        hostname = urlparse(link.url).hostname
        if hostname:
            hosts.add(hostname)

    for host in sorted(hosts):
        signal_suffix = host.replace(".", "_")

        try:
            socket.getaddrinfo(host, None)
            collector.record(client.slug, f"dns_{signal_suffix}", source="dns", ok=True, value={"resolves": True})
        except OSError as exc:
            collector.record(client.slug, f"dns_{signal_suffix}", source="dns", ok=False, error=_describe(exc))
            # No point attempting TLS against a name that does not resolve.
            continue

        try:
            context = ssl.create_default_context()
            with (
                socket.create_connection((host, 443), timeout=collector.timeout) as sock,
                context.wrap_socket(sock, server_hostname=host) as tls,
            ):
                cert = tls.getpeercert() or {}
            collector.record(
                client.slug,
                f"tls_{signal_suffix}",
                source="tls",
                ok=True,
                value={"not_after": cert.get("notAfter", "unknown")},
            )
        except Exception as exc:
            collector.record(client.slug, f"tls_{signal_suffix}", source="tls", ok=False, error=_describe(exc))


def _collect_repository(collector: Collector, http: Any, client: Client) -> None:
    """Repository activity from the GitHub or GitLab API.

    Unauthenticated requests are rate-limited; a 403 is recorded as a failed
    observation rather than raised, and `health.derive` treats a signal that was
    never successfully collected as absent rather than as evidence.
    """
    source_url = client.link_url("source")
    if not source_url:
        return

    github = _GITHUB_RE.match(source_url)
    if github:
        owner, repo = github.group(1), github.group(2).removesuffix(".git")
        _collect_github(collector, http, client.slug, owner, repo)
        return

    gitlab = _GITLAB_RE.match(source_url)
    if gitlab:
        _collect_gitlab(collector, http, client.slug, gitlab.group(1))
        return

    collector.record(
        client.slug,
        "repo_metadata",
        source="repo",
        ok=False,
        error="source host not recognised; no collector available",
    )


def _collect_github(collector: Collector, http: Any, slug: str, owner: str, repo: str) -> None:
    api = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        response = http.get(api, headers={"Accept": "application/vnd.github+json"})
    except Exception as exc:
        collector.record(slug, "repo_metadata", source="github", ok=False, error=_describe(exc))
        return

    if response.status_code != 200:
        collector.record(
            slug,
            "repo_metadata",
            source="github",
            ok=False,
            error=f"HTTP {response.status_code}",
        )
        return

    data = response.json()
    collector.record(
        slug,
        "repo_metadata",
        source="github",
        ok=True,
        value={
            "full_name": data.get("full_name"),
            "stars": data.get("stargazers_count"),
            "open_issues": data.get("open_issues_count"),
        },
    )
    collector.record(
        slug,
        "repo_archived",
        source="github",
        ok=True,
        value={"archived": bool(data.get("archived"))},
    )
    if data.get("pushed_at"):
        collector.record(
            slug,
            "repo_latest_commit",
            source="github",
            ok=True,
            value={"committed_at": data["pushed_at"]},
        )

    try:
        releases = http.get(f"{api}/releases/latest", headers={"Accept": "application/vnd.github+json"})
        if releases.status_code == 200:
            release = releases.json()
            collector.record(
                slug,
                "repo_latest_release",
                source="github",
                ok=True,
                value={"published_at": release.get("published_at"), "tag": release.get("tag_name")},
            )
        elif releases.status_code == 404:
            # A project with no releases is a fact, not a failure.
            collector.record(slug, "repo_latest_release", source="github", ok=True, value={"published_at": None})
    except Exception as exc:
        collector.record(slug, "repo_latest_release", source="github", ok=False, error=_describe(exc))


def _collect_gitlab(collector: Collector, http: Any, slug: str, project_path: str) -> None:
    from urllib.parse import quote

    api = f"https://gitlab.com/api/v4/projects/{quote(project_path, safe='')}"
    try:
        response = http.get(api)
    except Exception as exc:
        collector.record(slug, "repo_metadata", source="gitlab", ok=False, error=_describe(exc))
        return

    if response.status_code != 200:
        collector.record(slug, "repo_metadata", source="gitlab", ok=False, error=f"HTTP {response.status_code}")
        return

    data = response.json()
    collector.record(
        slug,
        "repo_metadata",
        source="gitlab",
        ok=True,
        value={"full_name": data.get("path_with_namespace"), "stars": data.get("star_count")},
    )
    collector.record(slug, "repo_archived", source="gitlab", ok=True, value={"archived": bool(data.get("archived"))})
    if data.get("last_activity_at"):
        collector.record(
            slug,
            "repo_latest_commit",
            source="gitlab",
            ok=True,
            value={"committed_at": data["last_activity_at"]},
        )


# --- persistence and reporting ---------------------------------------------


def _load_previous(root: Path) -> dict[tuple[str, str], Observation]:
    path = root / OBSERVATIONS_PATH
    if not path.is_file():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    previous: dict[tuple[str, str], Observation] = {}
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
        previous[(observation.client, observation.signal)] = observation
    return previous


def _write(root: Path, now: str, observations: dict[tuple[str, str], Observation]) -> None:
    """Write the observation file.

    Sorted and indented so the committed diff is readable, which is the whole
    point of a reviewable refresh (spec 36).
    """
    path = root / OBSERVATIONS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "client": observation.client,
            "signal": observation.signal,
            "observed_at": observation.observed_at,
            "source": observation.source,
            "ok": observation.ok,
            "value": observation.value,
            "error": observation.error,
        }
        for _, observation in sorted(observations.items())
    ]
    payload = {
        "schema_version": 1,
        "updated_at": now,
        "note": (
            "Generated by `make refresh-metadata`. Machine-collected; not hand-edited. "
            "Observations inform maintenance status but never overwrite editorial metadata."
        ),
        "observations": rows,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=False) + "\n", encoding="utf-8")


def _print_diff(
    previous: dict[tuple[str, str], Observation],
    current: dict[tuple[str, str], Observation],
) -> None:
    """Human-readable before/after per client (spec 36)."""
    changes: dict[str, list[str]] = {}

    for key, observation in sorted(current.items()):
        client, signal = key
        before = previous.get(key)
        after_text = _summarise(observation)
        before_text = _summarise(before) if before else None

        if before_text is None:
            changes.setdefault(client, []).append(f"  {signal}: (new) -> {after_text}")
        elif before_text != after_text:
            changes.setdefault(client, []).append(f"  {signal}: {before_text} -> {after_text}")

    if not changes:
        print("\nNo observation changed.")
        return

    print("\nChanged observations:")
    for client in sorted(changes):
        print(f"\n{client}")
        for line in changes[client]:
            print(line)


def _summarise(observation: Observation | None) -> str:
    if observation is None:
        return "(absent)"
    if not observation.ok:
        return observation.error or "failed"
    if not observation.value:
        return "ok"
    return ", ".join(f"{key}={value}" for key, value in sorted(observation.value.items()) if value is not None)


def _print_warnings(site: Site, merged: dict[tuple[str, str], Observation]) -> None:
    """Re-derive health from the new observations and report warnings only.

    These are conditions worth a human's attention, not conclusions. Nothing
    here changes a client's editorial status (spec 38, invariant 5).
    """
    from mastodon_clients.health import ObservationSet, derive

    by_client: dict[str, dict[str, Observation]] = {}
    for (client_slug, signal), observation in merged.items():
        by_client.setdefault(client_slug, {})[signal] = observation

    warnings: list[str] = []
    for client in site.clients:
        signals = by_client.get(client.slug)
        if not signals:
            continue
        result = derive(client, ObservationSet(client=client.slug, by_signal=signals))
        warnings.extend(f"  {warning.client}: {warning.message}" for warning in result.warnings)

    if warnings:
        print(f"\n{len(warnings)} condition{'s' if len(warnings) != 1 else ''} worth a look:")
        for line in warnings:
            print(line)
        print("\nThese are flags for review, not conclusions. No status was changed automatically.")


def _describe(exc: Exception) -> str:
    """A short, stable error string.

    Stable matters: an error message that embeds a timestamp or a socket number
    would produce a spurious diff on every refresh.
    """
    name = type(exc).__name__
    message = str(exc).strip()
    return f"{name}: {message}" if message else name
