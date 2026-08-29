# Mawkingbird Mastodon Web Client Review Site

## Product and Technical Specification

**Status:** Initial specification
**Site:** mawkingbird.com
**Owner/editor:** Matthew Martin
**Primary technology:** Pelican, Python, uv, Make, GitHub Actions, GitHub Pages

---

# 1. Purpose

Mawkingbird will be a static, editorially neutral directory and review site for **web clients compatible with the Mastodon.social REST API**.

The site's purpose is to help Mastodon users choose an appropriate web client based on concrete criteria such as:

* feature set
* intended audience
* maintenance activity
* project health
* funding model
* support status
* licensing/source availability
* deployment model
* hosting requirements
* availability of documentation and source code
* observable technical and operational signals

The site should be useful both to humans browsing interactively and to search engines, LLMs, and other machines consuming structured information.

The site should not attempt to aggressively promote or condemn individual products. Reviews should distinguish fact from interpretation, describe trade-offs, and avoid exaggerated praise or criticism.

---

# 2. Scope

## 2.1 Included products

A product qualifies for inclusion when:

1. it communicates with servers using the Mastodon-compatible REST API;
2. it is primarily intended to let users read, browse, post to, and otherwise interact with Mastodon-style social feeds;
3. it is usable through the web.

Examples may include:

* standalone hosted web clients
* self-hostable web clients
* alternative Mastodon web frontends
* clients bundled with another Mastodon-compatible server product
* clients that require a Mastodon server deployment in order to operate

The directory is concerned with the **web client**, not whether an equivalent native Android, iOS, macOS, Windows, or Linux application exists.

## 2.2 Excluded products

The directory should exclude utilities whose primary purpose is a narrow or one-off Mastodon task rather than general feed interaction.

Examples of excluded categories:

* account migration utilities
* mass preference-changing utilities
* bulk unfollow/follow tools
* correlation or discovery utilities such as Debirdify
* one-purpose moderation utilities
* analytics-only applications
* command-line scripts that do not operate as general clients

The distinction should be documented so that inclusion decisions remain consistent.

---

# 3. Editorial principles

Mawkingbird should use a restrained, factual editorial voice.

Reviews should:

* describe what a product does;
* distinguish observable facts from interpretation;
* describe notable strengths where supported by evidence;
* describe limitations where supported by evidence;
* avoid promotional language;
* avoid treating popularity as quality;
* avoid treating age as either inherently positive or negative;
* avoid declaring a client "dead" based on any single machine-generated signal.

Where uncertainty exists, the review should say so.

For example:

> The source repository has not had a release in 14 months, although the hosted site remains operational and recent commits exist.

is preferable to:

> This project is abandoned.

unless there is strong evidence that the project is actually abandoned.

---

# 4. Primary audiences

The site should support multiple user-oriented entry points rather than assuming there is one universally best Mastodon client.

Initial audience pages should include:

* New Mastodon users
* Power users
* Twitter/X refugees
* News junkies
* Content creators

Additional audiences may be added by defining metadata rather than altering the underlying architecture.

A client may suit multiple audiences.

Audience suitability should generally be based on observable features and review criteria rather than purely subjective editorial preference.

---

# 5. Core information architecture

The initial site should contain at least the following page classes.

## 5.1 Home page

The home page should explain what the directory is and provide immediate routes into the directory.

It should include:

* a short explanation of what a Mastodon web client is;
* selected audience entry points;
* a link to the full client directory;
* a short explanation of how products are reviewed;
* prominent disclosure of the relationship between Mawkingbird and the Mawkingbird Mastodon client;
* recently added or recently updated reviews, where appropriate.

The home page should not imply that Mawkingbird is an independent organization separate from its proprietor.

## 5.2 Client directory

Canonical URL:

`/clients/`

The directory must render useful HTML without JavaScript.

Each entry should expose enough information to make the directory useful before a visitor opens the full review.

Suggested visible fields include:

* client name
* short description
* availability/status
* open/closed/hybrid source status
* hosted/self-hosted/deployment type
* intended audiences
* maintenance status
* selected feature indicators
* rating
* last reviewed date

JavaScript should progressively enhance this page with features such as:

* client-side search
* sorting
* filtering
* multi-select filters
* hiding/showing columns

JavaScript must not be required for search engines or non-JavaScript users to discover every client.

## 5.3 Individual client review

Canonical form:

`/clients/<slug>/`

Each client page should include:

1. title
2. short summary
3. status
4. rating
5. who it is for
6. notable features
7. feature matrix
8. deployment model
9. source/licensing status
10. funding model
11. maintenance/project health
12. support information
13. important links
14. machine-collected signals
15. editorial prose
16. last review date
17. last automated metadata refresh date
18. related clients or category links

## 5.4 Audience landing pages

Examples:

* `/for/new-users/`
* `/for/power-users/`
* `/for/twitter-refugees/`
* `/for/news-junkies/`
* `/for/content-creators/`

These should be fully rendered static pages.

They may contain:

* brief audience-specific explanatory prose;
* relevant feature criteria;
* matching clients;
* sortable/filterable tables as progressive enhancement.

## 5.5 Feature/category landing pages

Examples:

* `/features/multi-account/`
* `/features/lists/`
* `/features/scheduled-posts/`
* `/open-source/`
* `/standalone/`
* `/hosted/`

The exact set should be generated from the structured metadata where practical.

## 5.6 Comparison pages

Comparison pages may exist, but pairwise comparison prose should **not** be manually authored or generated independently by an LLM.

A comparison URL might be:

`/compare/elk/phanpy/`

The page should instead be produced deterministically from the two clients' structured metadata.

Possible contents:

* side-by-side feature table
* licensing
* deployment model
* funding
* maintenance indicators
* audience classifications
* ratings and component scores
* links to the two full reviews

The number of possible pairwise pages grows quadratically. The build should therefore either:

1. generate comparisons only for known/popular requested pairs; or
2. generate comparisons dynamically at build time from a defined allow-list.

The project should not blindly generate every possible pair solely for SEO.

## 5.7 Dead/discontinued client pages

A removed or discontinued client should not simply disappear.

Its canonical URL should remain available with a minimal historical page containing, where known:

* client name
* former description
* former URLs
* source repository
* last known activity
* evidence of discontinuation
* date status was changed
* possible successor or alternative clients

These pages should clearly distinguish between:

* discontinued
* unmaintained
* inaccessible
* unknown
* temporarily unavailable

A dead domain by itself is not sufficient evidence that the software is discontinued.

## 5.8 About page

The About page should state clearly that:

* the site is operated by Matthew Martin;
* Matthew Martin maintains mawkingbird.com;
* Mawkingbird is itself a freemium Mastodon web client;
* Mawkingbird therefore has a commercial/editorial relationship to the subject matter being reviewed.

It should explain the site's editorial philosophy and scoring approach.

The disclosure should be prominent and written plainly rather than buried in legal language.

## 5.9 Submitting a client/correction

The site should tell readers that they may request a client or correction by:

* opening a GitHub issue; or
* contacting `@mistersql@mastodon.social`.

No account submission system is required.

---

# 6. Data architecture

Structured data should be the canonical source for facts.

Prose should sit on top of structured data rather than embedding important factual information only inside narrative text.

The system should distinguish at least four classes of information:

1. manually maintained structured metadata
2. LLM-generated prose
3. human prose overrides
4. machine-observed metadata

These classes should remain physically or logically separate.

---

# 7. Repository structure

A target repository structure could resemble:

```text
.
├── Makefile
├── pyproject.toml
├── uv.lock
├── pelicanconf.py
├── publishconf.py
├── README.md
│
├── data/
│   ├── clients/
│   │   ├── elk.toml
│   │   ├── phanpy.toml
│   │   └── ...
│   │
│   ├── taxonomy/
│   │   ├── features.toml
│   │   ├── audiences.toml
│   │   └── statuses.toml
│   │
│   └── generated/
│       ├── observations.json
│       ├── health.json
│       └── ...
│
├── content/
│   ├── pages/
│   ├── generated/
│   │   └── clients/
│   └── overrides/
│       └── clients/
│
├── prompts/
│   ├── client-review.md
│   └── refresh-review.md
│
├── scripts/
│   ├── build_content.py
│   ├── generate_review.py
│   ├── collect_metadata.py
│   ├── validate_data.py
│   ├── calculate_scores.py
│   └── ...
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── theme/
│
└── .github/
    └── workflows/
        ├── build.yml
        └── publish.yml
```

Exact names may change, but the conceptual separation is important.

---

# 8. Client TOML model

Anything intended for regular human or LLM editing should be TOML.

One file should represent one client.

Example:

```toml
schema_version = 1

slug = "example-client"
name = "Example Client"

status = "active"

homepage = "https://example.com/"
reviewed_at = "2026-08-29"

source_model = "open-source"
license = "AGPL-3.0-or-later"

deployment = "standalone"
funding_model = ["donations"]

audiences = [
    "new-users",
    "power-users",
]

[links]
homepage = "https://example.com/"
documentation = "https://docs.example.com/"
source = "https://github.com/example/client"
issues = "https://github.com/example/client/issues"
funding = "https://example.com/support"

[features]
multi_account = true
lists = true
filters = true
push_notifications = false
quote_posts = true
scheduled_posts = false
bookmarks = true
translation = true
local_timeline = true
federated_timeline = true
custom_emoji = true
content_warnings = true
moderation_controls = true

[review]
generated_file = "content/generated/clients/example-client.md"
override_file = "content/overrides/clients/example-client.md"
```

The actual schema should be validated.

Unknown arbitrary keys should preferably fail validation rather than silently passing through.

---

# 9. Link model

Product links are first-class data.

Links should not merely appear inside prose.

Each client may have multiple typed links.

Useful initial link types include:

* homepage
* hosted application
* canary/nightly site
* documentation
* source repository
* issue tracker
* release page
* changelog
* funding page
* support page
* privacy policy
* terms
* project/community page

A product may have multiple source repositories or deployments.

The data model should therefore support an eventual move from:

```toml
[links]
source = "..."
```

to richer repeated link records if necessary.

For example:

```toml
[[links]]
type = "source"
url = "https://github.com/foo/bar"
label = "Primary repository"

[[links]]
type = "canary"
url = "https://canary.example.com/"
```

Link metadata should eventually be capable of recording:

* URL
* type
* label
* expected content
* whether it should be automatically checked

---

# 10. Feature taxonomy

The initial feature taxonomy should include at least:

* multi-account support
* lists
* user/server filtering
* push notifications
* quote posts
* scheduled posts
* bookmarks
* translation
* local timeline
* federated timeline
* custom emoji
* content warnings
* moderation controls

The taxonomy should be extensible.

Additional likely fields include:

* column/deck layout
* keyboard navigation
* advanced search
* saved searches
* hashtag following
* thread view
* conversation context
* media galleries
* drafts
* polls
* post editing
* account notes
* follow requests
* profile editing
* server switching
* custom timelines
* notification filtering
* accessibility features
* mobile/responsive layout
* PWA/installability

A feature value should not necessarily be restricted permanently to Boolean values.

Some features are better represented as:

```text
yes
no
partial
unknown
not-applicable
```

The schema should anticipate this even if the initial implementation begins with booleans.

---

# 11. Source model

Clients should be classified as:

* `open-source`
* `closed-source`
* `hybrid`
* `unknown`

"Hybrid" can represent products where meaningful portions are open source but important deployed components are proprietary.

Where open source, the license should be recorded separately.

Source availability and license should not be conflated.

---

# 12. Deployment model

Clients should be classified separately by deployment characteristics.

Suggested values include:

* `hosted`
* `self-hostable`
* `hosted-and-self-hostable`
* `bundled-with-server`
* `unknown`

A separate field should identify whether the client can operate independently of deploying a Mastodon-compatible server.

For example:

```toml
standalone = true
```

or an enumerated model:

```toml
server_dependency = "independent"
```

versus:

```toml
server_dependency = "requires-server-deployment"
```

This distinction is important because some web clients cannot realistically be deployed as independent frontends.

---

# 13. Funding model

Initial funding values should include:

* commercial
* freemium
* donations
* sponsorship
* grants
* volunteer
* bundled-with-commercial-product
* unknown

Multiple values should be permitted.

Funding claims should ideally be backed by a corresponding source link.

---

# 14. Maintenance and project health

"Maintenance" must not be represented by a single metric.

The project should collect several signals and produce a conservative synthesized status.

Possible observations include:

* latest source commit
* latest release
* latest tagged version
* release cadence
* repository archived state
* website HTTP availability
* hosted application availability
* documentation availability
* issue tracker activity
* commit activity
* release/download page activity
* domain resolution
* TLS certificate validity
* known announcement of discontinuation

Possible derived status values:

* actively maintained
* maintained
* low activity
* possibly unmaintained
* unmaintained
* discontinued
* unknown

The derivation should be deterministic and documented.

The public site should make the underlying observations visible so users can understand why a status was assigned.

No single signal should be sufficient to classify a client as abandoned.

---

# 15. Machine metadata collection

Metadata collection should be implemented as an explicitly invoked job.

It should **not** run automatically on every Pelican build.

It should also **not initially be scheduled**.

Example command:

```sh
make refresh-metadata
```

That command may execute:

```sh
uv run python scripts/collect_metadata.py
```

Potential collectors include:

* HTTP endpoint checks
* DNS/domain checks
* TLS checks
* GitHub API
* GitLab API
* repository metadata
* release feeds
* Atom/RSS feeds
* project-specific release pages

The result should be written as generated JSON because it is code-consumed rather than human-authored.

Example:

```text
data/generated/observations.json
```

The generated file should be deterministic where practical.

A build should consume the most recently committed observation data without performing network requests.

This ensures that:

* builds are reproducible;
* the site still builds when third-party services are unavailable;
* Pelican builds remain fast;
* unexpected network activity cannot alter site content.

---

# 16. Observational data model

A machine observation should identify:

* client
* signal
* observed value
* observation timestamp
* source
* success/failure
* error, if any

Conceptually:

```json
{
  "client": "example-client",
  "signal": "homepage_http",
  "observed_at": "2026-08-29T14:20:00Z",
  "value": {
    "status": 200
  }
}
```

Machine observation history may initially retain only the latest value.

The architecture should permit historical observations later.

Historical records would make it possible to distinguish a one-day outage from a long-term disappearance.

---

# 17. Ratings

The site may use star ratings, but ratings must be derived from objectively countable or clearly defined criteria.

The rating should not represent an editor's personal impression.

A rating should be reproducible from structured metadata.

For example, component categories might include:

* breadth of supported core Mastodon features
* maintenance signals
* deployment/documentation completeness
* support/resources
* accessibility-related capabilities

Each component must define:

* what fields contribute points;
* how many points are available;
* how unknown values are handled;
* whether missing information lowers a score.

Scores should be calculated by code.

No LLM should assign a rating.

The scoring algorithm should be documented publicly.

The site should avoid pretending that a one-dimensional score captures every user's needs.

Audience pages and filtering should therefore remain more important than simply sorting all clients by stars.

---

# 18. Generated prose

LLM-generated prose should be generated only when explicitly requested.

LLM participation is an editorial tool, not part of the website runtime or ordinary build.

Example:

```sh
make generate-review CLIENT=phanpy
```

The command should:

1. load the selected client's TOML;
2. load relevant machine observations;
3. load the review prompt;
4. optionally retrieve or accept explicitly supplied source material;
5. generate prose only for that client;
6. write generated content only to that client's generated file;
7. leave every other review untouched.

Adding one new client must not require regenerating all existing reviews.

Likewise, refreshing one client's prose must not cause unrelated content changes.

---

# 19. LLM output constraints

The review-generation prompt should instruct the model to:

* use a neutral tone;
* avoid sales language;
* avoid ungrounded judgments;
* explicitly identify uncertainty;
* rely on supplied structured facts and sources;
* not invent features;
* not infer licensing without evidence;
* not describe a project as abandoned solely from inactivity;
* generate only prose fields;
* never rewrite human override content;
* never calculate ratings itself.

LLM-generated prose should be clearly separable from factual structured data.

---

# 20. Human prose overrides

Human prose overrides must survive all future LLM regeneration.

Generated prose and human overrides should therefore never occupy the same canonical source file unless there is an explicit safe merge mechanism.

A preferred model is:

```text
content/generated/clients/phanpy.md
content/overrides/clients/phanpy.md
```

At build time:

1. load generated prose;
2. load human overrides if present;
3. replace only matching named prose sections;
4. render the merged result.

Overrides should operate at section granularity.

For example:

```toml
[prose]
summary = """
...
"""

who_is_it_for = """
...
"""

maintenance = """
...
"""
```

or an equivalent Markdown/frontmatter structure.

A human should be able to override only `summary` while allowing all other sections to continue using generated text.

Deleting an override should restore the generated version.

---

# 21. Provenance

Where practical, generated prose should record provenance metadata such as:

* generation timestamp
* prompt version
* model identifier
* client data revision/hash
* source revision/hash

This information need not necessarily be displayed publicly.

Its purpose is reproducibility and editorial debugging.

---

# 22. Build pipeline

The ordinary site build should be completely offline with respect to third-party client sites.

Conceptually:

```text
TOML metadata
      +
generated observations JSON
      +
generated prose
      +
human prose overrides
      ↓
content assembly
      ↓
Pelican
      ↓
static HTML
      ↓
GitHub Pages
```

A typical build target:

```sh
make build
```

should roughly perform:

```sh
uv run python scripts/validate_data.py
uv run python scripts/calculate_scores.py
uv run python scripts/build_content.py
uv run pelican content
```

Exact implementation may differ.

---

# 23. Makefile interface

The Makefile should provide a discoverable developer interface.

Suggested targets:

```text
make setup
make build
make serve
make clean
make validate
make test
make generate-review CLIENT=<slug>
make refresh-review CLIENT=<slug>
make refresh-metadata
make score
make check-links
make publish
```

`make generate-review` should operate on exactly one client.

An optional explicit bulk command may exist:

```sh
make generate-all-reviews
```

but it should never be implied by the ordinary workflow.

---

# 24. Validation

A validation pass should run before every production build.

It should detect:

* duplicate slugs
* malformed URLs
* nonexistent taxonomy values
* unknown feature identifiers
* missing required fields
* invalid status values
* invalid date formats
* duplicate canonical URLs
* references to missing source files
* reviews without corresponding clients
* clients without review data where required
* invalid source/licensing combinations

A validation failure should stop the build.

Schema validation should be implemented in Python rather than relying only on conventions.

---

# 25. GitHub Actions

Initial workflows should focus on deterministic build and publication.

## Pull request / push checks

Run:

```text
uv sync --locked
make validate
make test
make build
```

The CI build should not contact client websites.

## Deployment

On an accepted push to the publishing branch:

```text
uv sync --locked
make build
deploy output/ to GitHub Pages
```

## Manual metadata refresh

Because metadata collection is not scheduled initially, GitHub Actions may optionally expose a manually dispatched workflow for:

```text
make refresh-metadata
```

This workflow should produce a commit or pull request containing changed observation JSON rather than silently altering the live site from transient network results.

The human editor can then inspect changes before publication.

---

# 26. SEO requirements

SEO is a core requirement rather than an afterthought.

Every meaningful directory facet should ideally have a real static URL and useful HTML.

## Baseline requirements

Each page should contain:

* unique `<title>`
* unique meta description
* canonical URL
* logical H1
* meaningful heading hierarchy
* server-rendered/internal static links
* crawlable content
* OpenGraph metadata
* appropriate social metadata
* stable URLs

The site should produce:

* `sitemap.xml`
* `robots.txt`
* RSS and/or Atom feeds where useful

## Internal linking

Client reviews should link naturally to:

* relevant features
* relevant audiences
* source-status categories
* deployment categories
* related clients

Audience and feature pages should link back to matching client reviews.

The site should therefore create a dense but meaningful internal-link graph without generating low-value SEO pages.

---

# 27. Structured data

Machine-readable data is part of the roadmap and should be anticipated in the initial content model.

Possible future outputs include:

```text
/clients.json
/clients/<slug>.json
/features.json
```

The HTML may include JSON-LD where useful.

Potential Schema.org types should be evaluated rather than forced onto entities that do not fit them cleanly.

The structured data should be derived from the same canonical TOML used to render the HTML.

There should not be separate manually maintained HTML facts and JSON facts.

---

# 28. Progressive enhancement

The site should follow a strict progressive-enhancement model.

HTML must contain the complete meaningful directory content.

JavaScript may provide:

* live search
* column sorting
* filtering
* multi-filter combinations
* client comparison selection
* URL/history updates for selected filters
* display preferences

JavaScript should not be responsible for obtaining the canonical client dataset before the page becomes useful.

A crawler, text browser, or visitor with JavaScript disabled should still be able to:

* find every client;
* read every review;
* navigate every category;
* understand important metadata.

---

# 29. Search and filtering

Initial directory filters should include:

* audience
* source model
* deployment model
* standalone/server-dependent
* maintenance status
* funding model
* individual features

Sorting should include at least:

* name
* rating
* latest known release/activity
* last reviewed
* maintenance status

The default ordering should not imply editorial ranking unless explicitly stated.

Alphabetical ordering is a suitable neutral default.

---

# 30. Indexability of filtered views

JavaScript-created arbitrary filter combinations should not automatically create crawlable URLs.

Only curated, useful facets should receive static landing pages.

For example:

```text
/open-source/
/for/new-users/
/features/multi-account/
```

are appropriate.

An arbitrary combination such as:

```text
?open-source=yes&multi-account=yes&translation=no&foo=bar
```

should generally remain a user-interface state rather than an SEO landing page.

This avoids creating enormous quantities of low-value near-duplicate pages.

---

# 31. Screenshots and imagery

The initial version may be intentionally text-heavy.

The data model should nevertheless leave room for:

* client logo
* client icon
* generated SVG category icons
* screenshots
* screenshot captions
* screenshot source URL
* screenshot capture date

LLM-generated SVGs may be used for generic site/category illustrations.

Product screenshots should eventually come from a reproducible capture process rather than from hallucinated/generated representations of actual products.

Images should not block launch.

---

# 32. Link checking

Links should be divided into two conceptual classes.

### Editorial links

Links intentionally associated with the product, such as documentation and source repositories.

### Observed state

The most recently observed result of checking those links.

This prevents a temporary network failure from deleting or overwriting the editorially recorded URL.

For example:

```text
Known homepage:
https://example.com/

Last check:
503 Service Unavailable at 2026-08-29
```

is preferable to removing the homepage.

---

# 33. Client lifecycle

Clients should have an explicit lifecycle status independent of automated health.

Suggested statuses:

```text
candidate
active
inactive
discontinued
excluded
```

`candidate` allows a record to exist before editorial review is finished.

`excluded` allows the repository to record that a known product was deliberately determined to be outside the site's scope without publishing it as an ordinary review.

Machine observations must not directly change this editorial lifecycle field.

---

# 34. Workflow for adding a client

A normal client addition should be approximately:

```text
1. Create data/clients/<slug>.toml.
2. Populate factual metadata and source links.
3. Run validation.
4. Refresh automated observations for that client.
5. Invoke the LLM to generate that client's prose.
6. Review/edit prose as needed.
7. Add human overrides where appropriate.
8. Build locally.
9. Commit.
10. CI validates and publishes.
```

At no point should adding client B require regeneration of client A.

---

# 35. Workflow for refreshing an existing review

An explicit review refresh should roughly be:

```sh
make refresh-metadata CLIENT=phanpy
make refresh-review CLIENT=phanpy
make build
```

The LLM should receive:

* current structured metadata
* current observations
* existing generated prose
* human overrides for context but not modification
* relevant links/source material

Only that client's generated prose may change.

Human override files must remain untouched.

---

# 36. Workflow for machine metadata updates

A metadata refresh should ideally generate a reviewable diff.

Example:

```text
Phanpy
  latest_commit:
    2026-07-14 → 2026-08-28

  homepage:
    200 → 200

Example Client
  homepage:
    200 → timeout
```

The process should not automatically rewrite review prose merely because observations changed.

A changed signal may eventually produce an editorial "review recommended" marker.

---

# 37. Editorial freshness

The system should separately expose:

* `reviewed_at`
* `observations_updated_at`

These represent different concepts.

A page could therefore say:

```text
Review last updated: May 12, 2026
Automated project signals checked: August 28, 2026
```

This lets current machine facts improve an older review without pretending that a human editorial review occurred.

---

# 38. Project-health alerts

Although jobs are not initially scheduled, the metadata system should be capable of detecting conditions worth human review.

Examples:

* homepage repeatedly unavailable
* repository archived
* source repository removed
* explicit discontinuation message found
* hosted client unavailable
* long interval since release combined with long interval since commit
* formerly active project becomes inactive across several signals

These should produce warnings rather than automatic editorial conclusions.

---

# 39. SEO content generation rules

Generated category pages should only exist where the page offers real navigational or explanatory value.

Pages should not be mass-created solely from every possible metadata combination.

A useful page should generally contain:

* a real user intent;
* an explanatory introduction;
* a meaningful set of matching clients;
* direct links to those reviews.

Audience pages are editorially important enough to justify custom introductory prose.

Feature pages may use templated explanatory text where appropriate.

Pairwise comparison pages should be entirely derived from factual structured data rather than individually LLM-authored.

---

# 40. Accessibility

The site should itself model good web-client behavior.

Requirements should include:

* semantic HTML
* usable keyboard navigation
* visible focus states
* table headers
* appropriate captions
* accessible form controls
* no JavaScript-only navigation
* reasonable contrast
* reduced-motion respect
* informative link text

Filtering controls should remain understandable to assistive technology.

---

# 41. Performance

The site should remain fundamentally static and lightweight.

Goals:

* no application framework required in the browser
* minimal JavaScript
* no mandatory third-party runtime dependencies
* limited tracking
* lightweight CSS
* fast first render
* useful HTML before JavaScript executes

The initial scale of approximately 10–20 clients does not justify a database or server-side search service.

---

# 42. Privacy and analytics

If analytics are introduced, they should not compromise the site's lightweight/static character.

Analytics are not required for launch.

The site should avoid requiring visitors to log in.

No visitor account system is needed.

---

# 43. Testing

Tests should cover at least:

* TOML parsing
* schema validation
* scoring
* taxonomy generation
* override merging
* URL generation
* dead-client handling
* content generation
* comparison generation
* machine observation ingestion

Golden-file or snapshot tests may be useful for generated content structures.

The test suite should specifically verify:

> regenerating one client does not alter another client's generated content.

and:

> regenerating an LLM review does not alter human prose overrides.

These are core architectural invariants.

---

# 44. Determinism

Ordinary site builds should be deterministic from committed repository contents.

Given the same Git commit and software dependencies, two builds should produce materially identical site output.

Therefore the ordinary build must not depend on:

* current HTTP responses
* current GitHub API responses
* an LLM
* DNS state
* current release feeds

Those inputs enter the repository only through explicit refresh operations.

---

# 45. Dependency management

Python dependencies should be managed through `uv`.

The repository should commit:

* `pyproject.toml`
* `uv.lock`

CI should use the lockfile.

Scripts should execute with:

```sh
uv run ...
```

The project should avoid undocumented global Python tooling.

---

# 46. Pelican responsibilities

Pelican should remain primarily responsible for turning prepared content and data into HTML.

Complex data processing should occur before or through clearly isolated Pelican plugins/scripts rather than being distributed unpredictably through templates.

Templates should concentrate on presentation.

Python code should concentrate on:

* validation
* data normalization
* scoring
* joins
* generated page definitions
* observation processing

This division should keep the system testable.

---

# 47. Canonical data rule

When the same information appears in multiple places, there should be a defined authority.

Recommended precedence:

1. explicit human-maintained structured TOML
2. human prose override
3. generated machine observations
4. LLM-generated prose

An LLM must never be treated as the canonical authority for a structured fact.

Machine observations should inform status but should not silently overwrite editorial metadata.

---

# 48. Public methodology

The site should publish its methodology.

This should explain:

* what qualifies as a client;
* what is excluded;
* how features are assessed;
* how ratings are calculated;
* how maintenance signals are collected;
* why no single maintenance signal is decisive;
* how commercial relationships are disclosed;
* how corrections may be submitted.

This page should improve both reader trust and maintainability by making implicit editorial rules explicit.

---

# 49. Initial launch target

A reasonable version-one target is:

* 10–20 reviewed clients
* home page
* full client directory
* individual client pages
* five initial audience pages
* principal feature/category pages
* About/disclosure page
* methodology page
* submission/correction instructions
* deterministic star scoring
* TOML client records
* prose override system
* manually invoked metadata collector
* progressive-enhancement directory filtering
* XML sitemap
* canonical metadata
* OpenGraph metadata
* CI validation and GitHub Pages deployment

Screenshots, historical monitoring, comprehensive comparison generation, and public JSON feeds may follow.

---

# 50. Suggested roadmap

## Phase 1 — Foundation

Implement:

* repository structure
* TOML schema
* feature taxonomy
* client lifecycle
* link model
* Pelican templates
* directory
* client review page
* audience pages
* basic scoring
* validation
* override merging
* GitHub Pages deployment

## Phase 2 — Editorial automation

Implement:

* per-client LLM generation
* prompt versioning
* provenance metadata
* targeted review refresh
* source-input tooling
* safeguards against cross-client regeneration

## Phase 3 — Project-health collection

Implement:

* HTTP checks
* repository checks
* release/activity checks
* observation JSON
* project-health synthesis
* human-readable metadata diffs
* manually dispatched GitHub Action

## Phase 4 — Discovery and SEO expansion

Implement:

* feature landing pages
* richer internal linking
* deterministic comparison pages
* structured data
* machine-readable client feeds
* related-client generation

## Phase 5 — Richer presentation

Potential additions:

* screenshots
* screenshot automation
* icons
* historical health charts
* change history
* improved comparison UI

---

# 51. Non-goals

The initial project is explicitly not intended to be:

* a native mobile-client review site;
* a native desktop-client review site;
* a general Fediverse software directory;
* a Mastodon utility directory;
* a real-time monitoring service;
* a SaaS application;
* a user-generated review platform;
* an automatically scheduled crawler;
* an LLM-generated content farm;
* a database-backed application;
* an exhaustive pairwise prose-comparison site.

---

# 52. Key architectural invariants

The following rules should be treated as requirements rather than implementation suggestions.

### Invariant 1

**A normal site build does not access an LLM or the public Internet.**

### Invariant 2

**Generating or refreshing one client review does not regenerate unrelated reviews.**

### Invariant 3

**Human prose overrides survive all LLM regeneration.**

### Invariant 4

**Structured facts are canonical; LLM prose is not.**

### Invariant 5

**A single machine signal cannot declare a project abandoned.**

### Invariant 6

**The complete essential directory is available in HTML without JavaScript.**

### Invariant 7

**JavaScript progressively enhances the site rather than constituting the site.**

### Invariant 8

**Pairwise comparisons derive from structured data and do not require pair-by-pair prose generation.**

### Invariant 9

**Known dead/discontinued clients retain useful historical pages.**

### Invariant 10

**Mawkingbird's proprietor and commercial relationship to the subject matter are disclosed clearly.**

---

# 53. Initial acceptance criteria

Version one can be considered operational when all of the following are true:

1. At least ten client TOML records validate successfully.
2. `make build` works without Internet access.
3. `make generate-review CLIENT=x` changes only client `x`.
4. Existing prose overrides survive `make generate-review`.
5. The directory contains every published client in server-rendered HTML.
6. Directory filtering works with JavaScript enabled.
7. Directory navigation remains useful with JavaScript disabled.
8. Every client has a stable canonical URL.
9. Audience pages exist for new users, power users, Twitter refugees, news junkies, and content creators.
10. Rating values are generated deterministically by code.
11. The methodology explains the rating formula.
12. Source/product links are represented as structured data.
13. Machine observation JSON can be generated independently of the Pelican build.
14. A broken domain does not automatically mark a product discontinued.
15. Dead/discontinued products can retain minimal historical pages.
16. GitHub Actions validates and builds pull requests.
17. The production branch deploys successfully to GitHub Pages.
18. Sitemap and canonical metadata are present.
19. About/methodology pages clearly disclose that Matthew Martin operates the site and maintains the freemium Mawkingbird Mastodon web client.
20. A reader can find instructions for proposing a client through GitHub or `@mistersql@mastodon.social`.

---

# 54. Design philosophy summary

The central architectural idea is:

> **Facts are structured, observations are generated, prose is replaceable, and publication is static.**

TOML represents editorially maintained facts.

JSON represents machine-produced facts intended for code.

LLM output represents draft editorial prose.

Human override files represent final editorial authority over prose.

Pelican combines those inputs into static, crawlable pages.

Network collection and LLM generation happen only as explicit editorial operations. Neither belongs in the normal website build.

This separation gives Mawkingbird a path to accumulate useful reviews over time without turning every content update into a site-wide regeneration event, while also allowing machine-collected project-health information to remain substantially fresher than the prose surrounding it.
