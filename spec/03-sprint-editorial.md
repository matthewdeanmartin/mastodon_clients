# Sprint 3 — Editorial automation

**Goal:** per-client LLM prose generation that cannot damage a neighbouring client or a human override.

## Commands (§18, §23)

```sh
make generate-review CLIENT=phanpy    # generate prose for exactly one client
make refresh-review  CLIENT=phanpy    # regenerate, with existing prose as context
make generate-all-reviews             # explicit bulk; never implied by any other target
```

Each writes **only** `content/generated/clients/<slug>.md`. The script refuses to run without a `CLIENT`, and after writing it asserts that no other generated file changed (§34, Invariant 2).

## Prompt (§19)

`prompts/client-review.md`, carrying a `prompt_version` header. It instructs the model to use a neutral tone, avoid sales language, name its own uncertainty, rely only on supplied structured facts and sources, never invent a feature, never infer a licence without evidence, never call a project abandoned from inactivity alone, never compute a rating, and never rewrite override content.

`prompts/refresh-review.md` additionally receives the existing generated prose and the human overrides — the latter strictly as read-only context.

## Prose sections

A generated file is a set of named sections with stable ids:

```text
summary, who_is_it_for, notable_features, deployment,
source_and_licensing, funding, maintenance, support, verdict
```

## Overrides (§20, Invariant 3)

`content/overrides/clients/<slug>.toml` holds a `[prose]` table keyed by those same section ids. At build time `overrides.merge()` replaces matching sections only; unmatched generated sections pass through untouched. Override files live in a separate tree and are never written by any generation command.

## Provenance (§21)

Each generated file records, in front matter: generation timestamp, prompt version, model identifier, a hash of the client TOML, and a hash of any supplied source material. Not displayed publicly by default; present for reproducibility and editorial debugging.

## LLM transport

The generator assembles the full prompt and writes it to `build/prompts/<slug>.md`. If `ANTHROPIC_API_KEY` is set it calls the API; otherwise it stops and prints the prompt path so prose can be produced elsewhere and pasted in. The ordinary site build touches neither path (Invariant 1).

## Tests

- Regenerating client A leaves every other generated file byte-identical.
- Regenerating leaves the override file byte-identical, and the merged output still shows the override text rather than the regenerated text.
