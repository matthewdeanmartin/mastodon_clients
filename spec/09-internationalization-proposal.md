# Internationalization without full-site retranslations

Proposal only. No paid translation jobs, new languages, or translation infrastructure have been run or implemented in this pass.

## Target languages

The target is **30 languages total: English as the source language and 29 translated languages**. This is the intended coverage, not a claim that these translations already ship. Release complete translated journeys in batches while keeping all 30 languages in the plan.

1. English
2. Japanese
3. German
4. French
5. Spanish
6. Portuguese
7. Italian
8. Dutch
9. Polish
10. Korean
11. Traditional Chinese
12. Russian
13. Turkish
14. Ukrainian
15. Swedish
16. Finnish
17. Czech
18. Catalan
19. Norwegian
20. Indonesian
21. Hindi
22. Vietnamese
23. Arabic
24. Bengali
25. Tamil
26. Telugu
27. Persian
28. Hebrew
29. Thai
30. Romanian

Traditional Chinese is explicitly the Chinese target. Arabic, Persian and Hebrew require right-to-left layout support. Regional variants for languages such as Portuguese and Norwegian remain an implementation choice to settle before translating; the list does not imply a particular regional variant.

## Recommendation

Translate small, stable content units once and keep the results in version control. A normal build reads those saved translations and never calls a model. A separate, explicit translation command prepares only missing or changed units for selected locales.

There is an unavoidable initial translation cost per language. After that, cost follows the amount of changed prose multiplied by the target languages, plus context and review overhead. A style or numeric-data update should require no translation calls.

## Reuse the app's existing approach

The app already has:

- mastodon_mock/ui/scripts/i18n-todo.mjs: missing/stale work orders based on source hashes.
- mastodon_mock/ui/scripts/i18n-batch.mjs: compact batches of missing keys. This currently selects missing keys; it should not be assumed to handle stale keys without integration with the work-order logic.
- mastodon_mock/ui/i18n-context/en.context.json and language glossaries: context and terminology.
- mastodon_mock/ui/src/app/i18n/locale.ts: separate production and in-progress locales.

Use the same concepts and share terminology with the app. Keep the directory's Python/Jinja build and the app's Angular runtime independent; sharing translations does not require sharing their rendering frameworks.

## Three kinds of content

1. Interface strings: stable IDs for navigation, buttons, labels, badges and table headers. Translate each shared label once per locale, even if used on 40 pages.
2. Editorial content: stable IDs for a paragraph, bullet, headline, description or review section. Store locale versions by ID. Preserve paragraph context so translation is natural; avoid splitting every sentence into isolated fragments.
3. Facts: feature booleans, ratings, URLs, product names, dates and counts remain shared data. Format numbers/dates locally and interpolate them into translated messages. A score change must not invalidate the review translation.

Proposed cache record: content ID, target locale, source-text hash, relevant context/glossary version, translated text, review status, provenance and a human-edit lock. A key rename should migrate the record rather than force a retranslation. Reuse identical text only when its meaning and context also match.

## Update workflow

- Extract content units deterministically; file moves, formatting and build timestamps do not count as wording changes.
- Compare source hashes with saved translation records. Prepare a dry-run list and estimated token volume per locale before a translation run.
- Batch only missing/stale units, including nearby context, the previous translation when available, and the relevant terminology. Do not send the repository or all dictionaries every time.
- Merge only the returned units. Human-edited translations stay protected; changed source creates a review item instead of overwriting them.
- Validate placeholders, links, markup, plurals and missing keys mechanically. Review headlines and Free/Plus promises carefully, then inspect layouts in long-text and right-to-left languages.
- Set an explicit per-run budget and locale list. Translation remains opt-in; ordinary builds and deployments spend zero translation tokens.
- Glossary changes should invalidate affected terms, not every translation globally. Preserve provenance without automatically retranslating merely because a newer model exists.

Example: a 100-word paragraph changes in a 20,000-word site. Updating the 29 translated languages translates that paragraph 29 times (roughly 2,900 source words plus necessary context), rather than all 20,000 words 29 times (580,000 source words). English is the source and adds no translation work. This is an illustration of workload, not a token-price quote.

## Search and language selection

Publish actual static HTML for each released translation at language-specific paths, such as /de/clients/mawkingbird/. Keep existing English URLs stable. Each translated page gets its own canonical URL, correct HTML language/direction, translated title/description, and reciprocal hreflang links to available counterparts, with an x-default fallback. Do not canonicalize all translations to English.

Offer a language picker using native language names. Suggest the browser language when a translation is available; avoid forced redirects that hide the page a visitor or crawler requested. Remember explicit choices and preserve the equivalent page when switching.

Do not publish English duplicates under untranslated language paths. Publish complete translated pages or coherent page groups as they are ready. Untranslated destinations should clearly lead to the English original. If source meaning changes, mark the translation stale for review; material Free/Plus changes should not leave an obsolete promise live. Cosmetic source edits can wait for the next translation batch.

## Rollout

First implement extraction, hashes, storage and a dry-run report with no translation API attached. Prove that a CSS edit queues zero units, one paragraph edit queues one unit per selected locale, and a human edit survives regeneration.

Then localize one complete visitor journey: home, directory, the two integration categories, Mawkingbird review, Free/Plus interstitial, and navigation. Coordinate language choices and terminology with the app so the outbound journey remains understandable. Test one language with longer text and one right-to-left layout early. Expand to the full 30-language target (English plus 29 translations) in batches as complete journeys are ready, then translate the review long tail.

## References

[Google: multilingual sites](https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites) and [localized page versions](https://developers.google.com/search/docs/specialty/international/localized-versions) describe language URLs and hreflang.

[GNU gettext: fuzzy entries](https://www.gnu.org/software/gettext/manual/html_node/Fuzzy-Entries.html) describes the established pattern of retaining prior translations while flagging changed source for review. The directory can use gettext/Babel for shared interface strings or a compatible keyed catalog; paragraph translation memory remains independent of that choice.
