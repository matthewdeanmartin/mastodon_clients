# Sprint 4 — Project health

**Goal:** machine observations that inform status without ever silently becoming editorial conclusions.

## Collection (§15)

```sh
make refresh-metadata              # all clients
make refresh-metadata CLIENT=elk   # one client
```

Runs `uv run python -m mawkingbird.cli refresh-metadata`. Explicitly invoked, never scheduled, never part of a Pelican build. Results land in `data/generated/observations.json`, which is committed; the site build consumes the committed file and makes zero network requests (§44, Invariant 1).

Collectors:

- HTTP reachability for every checkable link (homepage, hosted app, docs, source, issues).
- DNS resolution and TLS certificate validity for each distinct host.
- GitHub / GitLab repository metadata: latest commit, latest release, tag, archived flag, open issue activity.
- Release Atom/RSS feeds where a repository API is unavailable.

Output is deterministic: sorted keys, stable ordering, timestamps rounded to the second.

## Observation model (§16)

```json
{
  "client": "example-client",
  "signal": "homepage_http",
  "observed_at": "2026-08-29T14:20:00Z",
  "source": "http",
  "ok": true,
  "value": {"status": 200},
  "error": null
}
```

The file stores the latest value per `(client, signal)`. The shape leaves room for a history list later, so distinguishing a one-day outage from a genuine disappearance becomes a data change rather than a rewrite.

## Health synthesis (§14, Invariant 5)

`mawkingbird/health.py` derives one of `actively-maintained`, `maintained`, `low-activity`, `possibly-unmaintained`, `unmaintained`, `discontinued`, `unknown`.

Rules are deterministic, documented on `/methodology/`, and conservative:

- No single signal can produce `unmaintained` or `discontinued`.
- `discontinued` requires an explicit editorial lifecycle status or a recorded discontinuation announcement — never inference from a dead domain (§32, acceptance criterion 14).
- Missing signals produce `unknown`, not a downgrade to `unmaintained`.
- The client page renders the underlying observations, so a reader can see why a status was assigned.

## Editorial links versus observed state (§32)

An observation never overwrites a link in the client TOML. The page shows the editorially recorded URL alongside the last observed result:

```text
Known homepage: https://example.com/
Last check:     503 Service Unavailable at 2026-08-29
```

## Diffs and alerts (§36, §37, §38)

`make refresh-metadata` prints a human-readable before/after diff per client. Conditions worth human attention — repository archived, source repository removed, hosted app unavailable, long gaps in both commits and releases — are emitted as **warnings**, never as automatic status changes.

Pages surface `reviewed_at` and `observations_updated_at` as separate facts (§37):

```text
Review last updated: May 12, 2026
Automated project signals checked: August 28, 2026
```

## Tests

Observation ingestion, health derivation for each status, and a regression asserting that a failing homepage alone never yields `discontinued`.
