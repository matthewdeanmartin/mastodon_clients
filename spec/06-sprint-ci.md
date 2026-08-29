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

Triggered on push to `main` and by `workflow_dispatch`. Builds with `publishconf.py`, uploads `output/` with `actions/upload-pages-artifact`, and deploys it with `actions/deploy-pages`.

The repository's Pages source is set to **GitHub Actions**, so Pages waits for that artifact and watches no branch. This is worth stating because the first version of this workflow pushed a `gh-pages` branch instead — which reported success on every run while publishing nothing, since nothing was watching the branch. A deploy that cannot fail loudly is worse than one that fails.

The base URL comes from `actions/configure-pages` rather than being hard-coded, so the sub-path cannot drift from the repository name. Served from <https://matthewdeanmartin.github.io/mastodon_clients/>, with no `CNAME`; `SITE_URL` is the single value to change if a custom domain is added later.

Single production site: no canary, no test deployment, no mirror repository. A `github-pages` concurrency group with `cancel-in-progress: false` lets an in-progress deploy finish rather than cancelling it.

## `refresh-metadata.yml` — manual dispatch (§25)

Runs `make refresh-metadata` and opens a **pull request** containing the changed `observations.json`. It never pushes to `main` and never touches the live site directly, so transient network results cannot alter published content without a human looking at the diff.

## Acceptance sweep

The twenty criteria of §53 are checked off in [07-invariants.md](07-invariants.md), each tied to a test or a build artefact.
