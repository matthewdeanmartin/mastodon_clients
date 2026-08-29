# Sprint 6 — CI and deployment

**Goal:** deterministic validation on every pull request, and a single production deploy to GitHub Pages.

## Version pinning

Matched to `../mastodon_mock` so the two repositories do not drift and shared lint behaviour stays identical:

- Python **3.14** via `actions/setup-python` v6.2.0.
- `astral-sh/setup-uv` v8.2.0, `actions/checkout` v7.0.0, pinned to the same commit SHAs.
- `ruff>=0.16.4`, `mypy>=1.18.0`, `pytest>=8.4.0`.

All third-party actions are pinned to a commit SHA with the version in a trailing comment, and `persist-credentials: false` is set on every checkout.

## `build.yml` — pull request and push checks (§25)

```sh
uv sync --locked
make validate
make test
make build
```

Plus `make lint-check` and `make typecheck`. The CI build contacts no client website; a network call during a build is a bug, not a flake.

## `publish.yml` — production deploy

Triggered on push to `main` and by `workflow_dispatch`. Builds with `publishconf.py` and pushes `output/` to the `gh-pages` branch root via `.github/scripts/publish-gh-pages.sh`. Served from the project Pages URL <https://matthewdeanmartin.github.io/mastodon_clients/>, so the build uses a sub-path base and writes no `CNAME`; `SITE_URL` is the single value to change if a custom domain is added later.

Single production site: no canary, no test deployment, no mirror repository. A `gh-pages-branch` concurrency group with `cancel-in-progress: false` prevents two deploys racing.

## `refresh-metadata.yml` — manual dispatch (§25)

Runs `make refresh-metadata` and opens a **pull request** containing the changed `observations.json`. It never pushes to `main` and never touches the live site directly, so transient network results cannot alter published content without a human looking at the diff.

## Acceptance sweep

The twenty criteria of §53 are checked off in [07-invariants.md](07-invariants.md), each tied to a test or a build artefact.
