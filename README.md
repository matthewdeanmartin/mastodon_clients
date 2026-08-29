# Mawkingbird

A static directory and review site for Mastodon-compatible **web clients**, at
[mawkingbird.com](https://mawkingbird.com/).

Facts live in structured TOML, one file per client. Prose sits on top of that
data rather than hiding facts inside narrative. Ratings are computed by code.
Machine observations are collected by an explicitly invoked job and committed to
the repository, so an ordinary build reaches no third-party site at all.

**Disclosure:** the site is operated by Matthew Martin, who also maintains
Mawkingbird, a freemium Mastodon web client. This directory reviews a field in
which its author competes. See [`content/pages/about.md`](content/pages/about.md).

## Quick start

```sh
make setup      # install dependencies from the lockfile
make validate   # check every data file
make build      # build the site into output/
make serve      # build, then serve on http://localhost:8000/
make check      # lint, typecheck, test, validate, build
```

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/). CI runs Python 3.14.

## Layout

```text
data/clients/*.toml        one file per client -- the canonical facts
data/taxonomy/*.toml       features, audiences, comparison allow-list
data/generated/            machine observations (committed, never hand-edited)
content/pages/             hand-written pages; the generator never touches these
content/generated/clients/ LLM-drafted prose, one file per client
content/overrides/clients/ human prose overrides, which always win
content/_generated/        assembled by `make build`; do not edit
mawkingbird/               the data layer: validation, scoring, health, assembly
theme/mawkingbird/         Jinja templates, CSS, and the progressive-enhancement JS
prompts/                   versioned prompts for prose generation
spec/                      the specification and the sprint plan
```

## Adding a client

1. Write `data/clients/<slug>.toml`. Record what you can establish; leave
   anything else `unknown` rather than guessing.
2. `make validate` — unknown keys, unknown features, malformed URLs, and
   incoherent source/licence combinations are all hard errors.
3. `make refresh-metadata CLIENT=<slug>` to collect machine signals, then review
   and commit the observation diff.
4. `make generate-review CLIENT=<slug>` to draft prose. This writes only that
   client's file and fails if anything else changed.
5. Edit `content/overrides/clients/<slug>.toml` for any section you want to
   write yourself. Overrides survive every future regeneration.
6. `make build`, then commit.

Adding client B never requires regenerating client A.

## The rules this repository enforces

These are checked by tests rather than left to care. The full mapping is in
[`spec/07-invariants.md`](spec/07-invariants.md).

- **A build is offline.** No HTTP, no GitHub API, no LLM, no DNS. Enforced by an
  import-graph test, not by hoping.
- **Generation touches one client.** The generator hashes every other review
  before and after, and fails on collateral damage.
- **Human overrides always win.** Nothing in the generator writes to the override
  tree, and the merge is section-granular.
- **No single signal declares a project abandoned.** A dead domain, a quiet
  repository, or an archive flag each reach `possibly-unmaintained` at worst.
  `discontinued` requires recorded evidence and a human's decision.
- **The directory works without JavaScript.** Every client is in the
  server-rendered HTML; the script filters rows that are already there.

## Machine-readable output

`/clients.json`, `/clients/<slug>.json`, and `/features.json` are generated from
the same records that render the HTML, so the two cannot disagree.

## Corrections

Open an issue, or contact
[@mistersql@mastodon.social](https://mastodon.social/@mistersql). Corrections
that resolve an `unknown` are the most useful kind — unknown values lower a
client's rating, so an under-researched client scores below what it deserves.

## Licence

MIT. See [LICENSE](LICENSE).
