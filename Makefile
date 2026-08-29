UV ?= uv
MAKEFLAGS += --no-print-directory
# Windows consoles default to cp1252, which cannot encode the star glyphs the
# score output uses. Forcing UTF-8 keeps `make score` working everywhere.
export PYTHONUTF8 := 1

PACKAGE := mastodon_clients
PYTHON_TARGETS := mastodon_clients tests
OUTPUT := output
SITE_URL ?= https://matthewdeanmartin.github.io/mastodon_clients

.PHONY: \
	help setup sync \
	validate score build build-prod serve clean \
	test lint lint-fix format typecheck check check-ci \
	generate-review refresh-review generate-all-reviews \
	refresh-metadata check-links \
	publish

help:
	@echo "Targets:"
	@echo "  setup                  Install dependencies from the lockfile"
	@echo ""
	@echo "  validate               Validate every data file (blocks the build)"
	@echo "  score                  Print the computed ratings"
	@echo "  build                  Full local build -> $(OUTPUT)/"
	@echo "  build-prod             Production build with absolute URLs"
	@echo "  serve                  Build, then serve $(OUTPUT)/ on :8000"
	@echo "  clean                  Remove generated content and $(OUTPUT)/"
	@echo ""
	@echo "  test                   Run the test suite"
	@echo "  lint                   Ruff check (read-only)"
	@echo "  lint-fix               Ruff check --fix, then format"
	@echo "  format                 Ruff format"
	@echo "  typecheck              mypy strict"
	@echo "  check                  Local quality gate: lint, typecheck, test, validate, build"
	@echo "  check-ci               Same, without formatting mutations"
	@echo ""
	@echo "  generate-review CLIENT=<slug>   Generate prose for exactly one client"
	@echo "  refresh-review  CLIENT=<slug>   Regenerate one client's prose with context"
	@echo "  generate-all-reviews            Explicit bulk generation (never implied)"
	@echo ""
	@echo "  refresh-metadata [CLIENT=<slug>]  Collect machine observations (NETWORK)"
	@echo "  check-links                       Report on the last collected link checks"

setup sync:
	@$(UV) sync --locked

# ── Data ──────────────────────────────────────────────────────────────────────

validate:
	@$(UV) run python -m mastodon_clients.cli validate

score: validate
	@$(UV) run python -m mastodon_clients.cli score

# ── Build ─────────────────────────────────────────────────────────────────────
#
# The whole pipeline is offline. It reads committed data only: no HTTP, no
# GitHub API, no LLM, no DNS (spec 44, invariant 1). A network call here is a
# bug, not a flake.

build: validate
	@$(UV) run python -m mastodon_clients.cli build-content
	@$(UV) run pelican content -s pelicanconf.py -o $(OUTPUT)
	@$(UV) run python -m mastodon_clients.cli sitemap --output $(OUTPUT) --site-url $(SITE_URL)

build-prod: validate
	@$(UV) run python -m mastodon_clients.cli build-content
	@SITE_URL_OVERRIDE=$(SITE_URL) $(UV) run pelican content -s publishconf.py -o $(OUTPUT)
	@$(UV) run python -m mastodon_clients.cli sitemap --output $(OUTPUT) --site-url $(SITE_URL)

serve: build
	@echo "Serving $(OUTPUT)/ at http://localhost:8000/"
	@$(UV) run python -m http.server 8000 --directory $(OUTPUT)

clean:
	@rm -rf $(OUTPUT) content/_generated content/extra build
	@echo "Removed $(OUTPUT)/, content/_generated/, content/extra/, and build/."

# ── Quality ───────────────────────────────────────────────────────────────────

test:
	@$(UV) run pytest

lint:
	@$(UV) run ruff check $(PYTHON_TARGETS)

lint-fix:
	@$(UV) run ruff check --fix $(PYTHON_TARGETS)
	@$(UV) run ruff format $(PYTHON_TARGETS)

format:
	@$(UV) run ruff format $(PYTHON_TARGETS)

typecheck:
	@$(UV) run mypy

check: lint typecheck test validate build
	@echo "All checks passed."

check-ci: lint typecheck test validate build
	@echo "CI checks passed."

# ── Editorial (LLM) ───────────────────────────────────────────────────────────
#
# Explicitly invoked, never part of `build`. Each command writes exactly one
# client's generated prose and asserts afterwards that nothing else changed
# (invariant 2). Human override files are never written by any of these
# (invariant 3).

generate-review:
	@test -n "$(CLIENT)" || { echo "Usage: make generate-review CLIENT=<slug>"; exit 1; }
	@$(UV) run python -m mastodon_clients.cli generate-review $(CLIENT)

refresh-review:
	@test -n "$(CLIENT)" || { echo "Usage: make refresh-review CLIENT=<slug>"; exit 1; }
	@$(UV) run python -m mastodon_clients.cli generate-review $(CLIENT) --refresh

# Bulk generation exists but is never implied by another target, so the ordinary
# workflow cannot accidentally rewrite every review (spec 18).
generate-all-reviews:
	@echo "Generating every review. This is the explicit bulk path; ordinary work should"
	@echo "use 'make generate-review CLIENT=<slug>' instead."
	@for toml in data/clients/*.toml; do \
		slug=$$(basename "$$toml" .toml); \
		echo "--- $$slug"; \
		$(UV) run python -m mastodon_clients.cli generate-review "$$slug" || exit 1; \
	done

# ── Machine metadata (NETWORK) ────────────────────────────────────────────────
#
# The only target that reaches the network. Not scheduled, and never invoked by
# a build (spec 15). It writes data/generated/observations.json, which is then
# committed and reviewed like any other change.

refresh-metadata:
	@$(UV) sync --extra collect
	@$(UV) run python -m mastodon_clients.cli refresh-metadata $(if $(CLIENT),--client $(CLIENT),)

check-links: validate
	@$(UV) run python -m mastodon_clients.cli validate

# ── Publish ───────────────────────────────────────────────────────────────────

publish: build-prod
	@echo "Built $(OUTPUT)/ for $(SITE_URL)."
	@echo "Deployment runs in GitHub Actions (.github/workflows/publish.yml)."
