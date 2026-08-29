# Mastodon Web Clients — Sprint Plan

Implementation plan for `spec/spec.md`. Each sprint has its own doc in `spec/`.

## Decisions (confirmed with owner, 2026-08-29)

| Question | Decision |
| --- | --- |
| Client seed data | Real, well-known Mastodon web clients, seeded from model knowledge plus targeted web research. Facts recorded conservatively; anything uncertain uses `unknown` rather than a guess. |
| Roadmap scope | Phases 1–3 in full, plus a thin slice of Phase 4 (JSON feeds, comparison pages, related clients). |
| Tooling | **Minimal**: `ruff`, `mypy`, `pytest`. No pylint/bandit/vulture/crosshair/etc. Versions and Python pinned to match `../mastodon_mock` so shared GitHub Actions lint behaviour matches. |
| Deployment | Single production deploy: Pelican `output/` pushed to the `gh-pages` branch root, served at <https://matthewdeanmartin.github.io/mastodon_clients/>. No custom domain, no canary, no test site, no mirror repo. |

## Pinned versions

Chosen to match `mastodon_mock` so CI does not diverge:

- Python **3.14** in GitHub Actions (`actions/setup-python`), `requires-python = ">=3.11"` locally.
- `astral-sh/setup-uv` v8.2.0, `actions/checkout` v7.0.0 — pinned to the same commit SHAs used by `mastodon_mock`.
- `ruff>=0.16.4`, `mypy>=1.18.0`, `pytest>=8.4.0`, `pytest-cov>=6.0.0`.
- `line-length = 120`, `target-version = "py311"`, ruff `preview = true` with `explicit-preview-rules = true`.

## Sprints

| Sprint | Doc | Theme | Spec sections |
| --- | --- | --- | --- |
| 1 | [01-sprint-foundation.md](01-sprint-foundation.md) | Repo skeleton, schema, validation, scoring | 7, 8, 9, 10–14, 17, 24, 45 |
| 2 | [02-sprint-site.md](02-sprint-site.md) | Pelican build, templates, all page types | 5, 22, 26–31, 40, 41, 46 |
| 3 | [03-sprint-editorial.md](03-sprint-editorial.md) | LLM prose generation, overrides, provenance | 18–21, 34, 35, 47 |
| 4 | [04-sprint-health.md](04-sprint-health.md) | Metadata collection, observations, health synthesis | 14–16, 32, 36–38 |
| 5 | [05-sprint-discovery.md](05-sprint-discovery.md) | JSON feeds, comparisons, related clients, seed data | 5.6, 27, 39, Phase 4 |
| 6 | [06-sprint-ci.md](06-sprint-ci.md) | GitHub Actions, Pages deploy, acceptance sweep | 25, 44, 53 |

## Invariants tracked across all sprints

The ten invariants in spec §52 are treated as acceptance tests, not aspirations.
[07-invariants.md](07-invariants.md) maps each invariant to the test that enforces it.
