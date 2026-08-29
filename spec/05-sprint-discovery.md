# Sprint 5 — Discovery, seed data, and the Phase 4 slice

**Goal:** populate the directory with real clients and add the structured-data surface.

## Seed data

Ten to twenty real Mastodon-compatible web clients, one TOML per client. Facts are recorded conservatively: anything not confidently known is `unknown` rather than a guess, since §19 and §47 make structured TOML the canonical authority and a wrong fact there propagates into scores, facets, and JSON output.

Each record carries `reviewed_at`, typed links, feature values, source model, licence, deployment model, server dependency, funding model, and audiences. At least one record exercises the discontinued lifecycle so §5.7 has live coverage.

Inclusion follows §2.1; the exclusion cases of §2.2 are documented on `/methodology/` so future decisions stay consistent. Products deliberately considered and rejected may be recorded with lifecycle `excluded`, which keeps the decision in the repository without publishing a review (§33).

## Machine-readable output (§27)

Emitted during the build from the same canonical TOML — never separately maintained:

- `/clients.json` — the full directory.
- `/clients/<slug>.json` — one client.
- `/features.json` — the taxonomy.

## Comparison pages (§5.6, Invariant 8)

`/compare/<a>/<b>/`, generated **only** for pairs listed in `data/taxonomy/comparisons.toml`. Content is derived entirely from structured data — side-by-side feature table, licensing, deployment, funding, maintenance indicators, audiences, component scores, links to both reviews. No pairwise prose is authored or generated. The quadratic blow-up of generating every pair is explicitly not done (§39).

## Related clients

Derived from shared audiences, feature overlap, and matching source/deployment model. Rendered on each client page to build the dense-but-meaningful internal link graph of §26, without creating new URLs.

## Done when

At least ten records validate, the directory renders them all, and the JSON endpoints agree with the HTML because both come from one source.
