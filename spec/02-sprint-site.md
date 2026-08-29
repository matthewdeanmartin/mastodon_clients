# Sprint 2 — Static site

**Goal:** every page type in spec §5 renders from the Sprint 1 data layer, with no JavaScript required.

## Build pipeline (§22)

`make build` runs, in order:

```sh
uv run python -m mastodon_clients.cli validate
uv run python -m mastodon_clients.cli score
uv run python -m mastodon_clients.cli build-content
uv run pelican content -s publishconf.py
```

`build-content` is the join step: it reads TOML, observations, generated prose and overrides, then writes Pelican-ready Markdown into `content/` with complete front matter. Pelican itself only turns prepared content into HTML (§46) — no data processing lives in templates.

## Pages

| URL | Source |
| --- | --- |
| `/` | hand-written page plus generated highlights |
| `/clients/` | full directory table, every client, server-rendered |
| `/clients/<slug>/` | one page per client, the eighteen sections of §5.3 |
| `/for/<audience>/` | five audience pages, intro prose from taxonomy |
| `/features/<feature>/` | one per feature flagged `page = true` |
| `/open-source/`, `/hosted/`, `/standalone/` | source and deployment facets |
| `/about/`, `/methodology/`, `/submit/` | editorial pages |
| `/sitemap.xml`, `/robots.txt`, feeds | generated during the build |

Discontinued clients keep their `/clients/<slug>/` URL and get a historical page (§5.7, Invariant 9) that distinguishes discontinued / unmaintained / inaccessible / unknown / temporarily-unavailable.

## Theme

`theme/mastodon_clients/` — Jinja templates plus one hand-written stylesheet. No CSS or JS framework (§41).

- Semantic HTML, real `<table>` with `<th scope>` and `<caption>`, visible focus states, `prefers-reduced-motion` honoured (§40).
- Per-page unique `<title>`, meta description, canonical link, OpenGraph tags (§26).
- JSON-LD on client pages, derived from the same TOML that renders the HTML (§27) — no second set of hand-maintained facts.

## Progressive enhancement (§28, §29)

`static/js/directory.js` — small, dependency-free. It enhances `/clients/` with live search, column sorting, and multi-select filters operating over the **already-rendered** table rows. It reads the DOM; it never fetches the dataset. Filter state goes in the URL fragment, not the query string, so arbitrary filter combinations never become crawlable URLs (§30). Delete the script and the page stays fully usable.

Sorting offers name, rating, latest activity, last reviewed, maintenance status. Default order is alphabetical, stated on the page as a neutral default rather than a ranking.

## Done when

`make build` produces a site fully navigable with JavaScript disabled, and every client is reachable from `/clients/`.
