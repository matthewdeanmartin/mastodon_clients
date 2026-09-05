# Invariants and acceptance criteria

The ten invariants of spec §52 are requirements, not suggestions, so each one is
tied to the code or test that enforces it. Where an invariant is enforced
structurally — by a module that cannot do the wrong thing — that is noted, since
a structural guarantee is stronger than a test.

## The ten invariants

| # | Invariant | Enforced by |
| --- | --- | --- |
| 1 | A normal site build does not access an LLM or the public Internet | `test_invariants.py::test_the_build_path_never_imports_the_collector` walks the import graph of every build-path module and fails on `httpx`, `socket`, `ssl`, `anthropic`, or `mastodon_clients.collect`. A module never imported cannot make a request. |
| 2 | Generating one review does not regenerate unrelated reviews | `generate.py` hashes every other generated file before and after the write and fails on any difference. Tested both ways: `test_generating_one_review_leaves_other_reviews_byte_identical` and `test_generation_reports_collateral_damage`, which simulates the failure and asserts the guard catches it. |
| 3 | Human prose overrides survive all LLM regeneration | Structural: no code path in `generate.py` writes to `content/overrides/`. Also checked — `_hash_override_tree` excludes nothing, not even the client being regenerated. Tested by `test_regeneration_leaves_human_overrides_byte_identical` and `test_the_override_still_wins_after_regeneration`. |
| 4 | Structured facts are canonical; LLM prose is not | Ratings come from `scoring.py`, which reads only structured data. The rating is stripped from the generation prompt entirely, so a model cannot see a score to justify. |
| 5 | A single machine signal cannot declare a project abandoned | `health.derive` requires corroboration from independent signals for every downgrade below `low-activity`, and `discontinued` is not derivable at all. Six tests in `test_health.py` cover the individual signals: dead homepage, long inactivity, archived repository, missing repository. |
| 6 | The complete essential directory is available in HTML without JavaScript | The directory table is server-rendered in full; `directory.js` reads the DOM and never fetches. `test_every_client_appears_in_the_generated_directory` checks completeness before any script runs. |
| 7 | JavaScript progressively enhances rather than constituting the site | The filter form ships `hidden` and is revealed by the script, so a visitor without JavaScript is never shown controls that cannot work. Removing the script leaves a complete page. |
| 8 | Pairwise comparisons derive from structured data | `_write_comparisons` renders only pairs listed in `comparisons.toml`, entirely from `client_payload`. No pairwise prose exists anywhere in the system. |
| 9 | Known dead clients retain useful historical pages | A discontinued client keeps its canonical URL and renders through `historical.html`. `test_a_discontinued_client_keeps_its_page_and_url` checks the URL, the listing, and the template. |
| 10 | The proprietor's commercial relationship is disclosed clearly | The disclosure is in the footer of every page in `base.html`, not only on `/about/`. Mawkingbird also appears in the directory as an ordinary entry, scored by the same code. |

## Acceptance criteria (spec §53)

| # | Criterion | Status |
| --- | --- | --- |
| 1 | At least ten client TOML records validate | 12 records; `make validate` passes |
| 2 | `make build` works without Internet access | Yes — invariant 1 above |
| 3 | `make generate-review CLIENT=x` changes only client x | Yes — invariant 2 |
| 4 | Prose overrides survive generation | Yes — invariant 3 |
| 5 | The directory contains every published client in server-rendered HTML | Yes — invariant 6 |
| 6 | Directory filtering works with JavaScript enabled | `static/js/directory.js`: search, sort, multi-select filters |
| 7 | Navigation remains useful with JavaScript disabled | Yes — invariant 7 |
| 8 | Every client has a stable canonical URL | `/clients/<slug>/`, stable across lifecycle changes |
| 9 | Five audience pages exist | new-users, power-users, twitter-refugees, news-junkies, content-creators |
| 10 | Ratings are generated deterministically by code | `scoring.py`; `test_scoring_is_deterministic` |
| 11 | The methodology explains the rating formula | `/methodology/scoring/`, rendered from `describe_components()` |
| 12 | Product links are structured data | `Link` records, both TOML forms supported |
| 13 | Observation JSON generates independently of the build | `make refresh-metadata`, never invoked by `make build` |
| 14 | A broken domain does not mark a product discontinued | `test_dead_homepage_alone_does_not_mark_a_client_discontinued` |
| 15 | Dead products retain historical pages | Yes — invariant 9; Pinafore and Hyperspace are live examples |
| 16 | GitHub Actions validates and builds pull requests | `.github/workflows/build.yml` |
| 17 | The production branch deploys to GitHub Pages | `.github/workflows/publish.yml` |
| 18 | Sitemap and canonical metadata are present | `sitemap.py`; canonical and OpenGraph tags in every template |
| 19 | About/methodology disclose the commercial relationship | `/about/` and `/methodology/`, plus the footer of every page |
| 20 | Instructions for proposing a client are findable | `/submit/`, linked from the footer of every page |

## Two notes on how this turned out

**Authorship is clear.** Every page credits Matthew Martin, creator of Mawkingbird. Marketing and useful comparisons are explicit purposes of the site; ratings retain their common calculation while needs guide the initial choice.

**Several clients sit at `inactive` rather than `discontinued`.** Semaphore's
repository is archived and Cuckoo+ has not seen a commit since 2022, both of
which look like endings. Neither has a recorded announcement, so neither is
marked discontinued — invariant 5 in practice rather than in principle. Pinafore
and Hyperspace *are* marked discontinued, because both have explicit evidence: a
retirement post and a maintainer-archived repository respectively.
