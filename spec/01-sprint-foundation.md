# Sprint 1 — Foundation

**Goal:** a validated, scored, testable data layer with no website attached yet.

## Deliverables

### Project scaffolding

- `pyproject.toml` — `uv`-managed, minimal dev group (`ruff`, `mypy`, `pytest`, `pytest-cov`) plus runtime deps (`pelican`, `markdown`).
- `uv.lock` committed.
- `Makefile` with the spec §23 interface.
- `.gitignore` additions: `output/`, `cache/`, `build/`.

### Package layout

```text
mastodon_clients/
  __init__.py
  models.py        # dataclasses for Client, Link, Feature, Observation
  schema.py        # TOML -> model parsing + strict validation
  taxonomy.py      # loads data/taxonomy/*.toml
  scoring.py       # deterministic star ratings
  overrides.py     # prose section merge
  health.py        # observation -> derived maintenance status
  errors.py
  cli.py
```

### Data

- `data/taxonomy/features.toml` — the §10 taxonomy. Each feature has `id`, `label`, `description`, `core` (counts toward feature breadth), and `page` (whether it gets a landing page).
- `data/taxonomy/audiences.toml` — the five §5.4 audiences plus intro prose and the feature criteria that matter to each.
- `data/taxonomy/statuses.toml` — lifecycle (§33), source models (§11), deployment models (§12), server dependency, funding models (§13), health statuses (§14).
- `data/clients/*.toml` — seeded properly in Sprint 5; two records here to exercise the pipeline.

### Schema rules (§8, §24)

- `schema_version` required, currently `1`.
- **Unknown keys are a hard error** at every level of the document.
- Feature values accept `true | false | "yes" | "no" | "partial" | "unknown" | "not-applicable"` and normalise to a `FeatureValue` enum. §10 requires the model to anticipate non-boolean values even though seed data is mostly boolean.
- Links parse from **both** the `[links]` table form and the `[[links]]` array-of-tables form (§9); the array form is canonical internally, so the eventual migration needs no code change downstream.
- Validation detects every condition listed in §24. Errors accumulate — the validator reports all problems at once rather than dying on the first.

### Scoring (§17)

Five components, documented in `mastodon_clients/scoring.py` and rendered verbatim on `/methodology/`:

| Component | Max | Source |
| --- | --- | --- |
| Feature breadth | 40 | fraction of `core` features present; `partial` counts half; `unknown` scores 0 and is reported separately |
| Maintenance | 25 | derived health status only, never a single raw signal |
| Deployment and docs | 15 | documentation link, source link, deployment model known, self-host instructions |
| Support and resources | 10 | issue tracker, support/community link, changelog |
| Accessibility | 10 | accessibility-related feature flags |

Total 100, converted to stars in half-star steps. Unknowns lower a score — stated plainly in the methodology — and never raise one.

## Tests

`tests/test_schema.py`, `tests/test_scoring.py`, `tests/test_taxonomy.py`, `tests/test_overrides.py`: TOML parsing, unknown-key rejection, duplicate slug detection, malformed URL detection, score determinism, override merge granularity.

## Done when

`make validate` and `make test` pass on the seed records, and scores are byte-reproducible across runs.
