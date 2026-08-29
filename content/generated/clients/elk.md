---
slug: elk
generated_at: 2026-08-29T00:00:00Z
prompt_version: 1
model: claude-opus-5
client_hash: seed
source_hash: none
---

<!-- section: summary -->

Elk is a general-purpose Mastodon web client built by contributors associated
with the Vue and Nuxt ecosystems. It presents a single compact reading column
rather than a deck, and runs either at its hosted instance or from a deployment
of your own against any Mastodon-compatible server.

<!-- section: who_is_it_for -->

Elk suits a reader who wants an alternative to the stock interface without
learning a new set of conventions to get it. The single-column layout and
multi-account support cover most everyday use, and nothing about it requires
configuration before it is usable.

It is a poorer fit for anyone who wants several timelines visible at once: Elk
does not offer a column or deck layout, and no amount of window width changes
that. Readers who want that arrangement should look at a client that provides
it explicitly.

<!-- section: notable_features -->

Multi-account support, lists, filters, and web push notifications are all
present. Post editing, polls, bookmarks, and hashtag following are supported, as
are drafts and translation.

Two features are recorded as partial. Keyboard navigation exists but is not
comprehensive, and search is more limited than the server's full search
capability. Where the extent of either matters to you, it is worth trying before
committing.

Quote posts and scheduled posts are not supported.

<!-- section: deployment -->

Elk can be used at its hosted instance or deployed yourself, and it works
against any Mastodon-compatible server rather than requiring one of its own.
That distinction matters: it means using Elk needs nothing more than an existing
account on an existing server.

A canary deployment tracking the main branch is published separately from the
stable instance.

<!-- section: source_and_licensing -->

The source is public and carries the MIT licence.

<!-- section: funding -->

Funded through donations and sponsorship, with a GitHub Sponsors page for the
project. The hosted instance is a volunteer-funded service rather than a
commercial product, which is worth knowing if you intend to depend on it: its
continued availability rests on the maintainers' willingness to keep running it.
The client can be self-hosted, so that dependency is avoidable.

<!-- section: maintenance -->

Recorded as actively maintained. The most recent commit observed was within the
last two weeks, and a tagged release was published within the last month. The
source repository is not archived and its homepage and hosted instance both
responded normally at the last check.

<!-- section: support -->

An issue tracker is available on the source repository. No separate
documentation site, support channel, or changelog is recorded, so questions
generally go to the issue tracker.

<!-- section: verdict -->

Elk is a straightforward single-column client that works against any server and
asks nothing of the reader up front. The trade-off is deliberate: it does not
offer a deck layout, scheduled posts, or quote posts, and its keyboard support
and search are both partial. For a reader who wants those things it is the wrong
client; for one who wants an unfussy reading column, the omissions cost nothing.
