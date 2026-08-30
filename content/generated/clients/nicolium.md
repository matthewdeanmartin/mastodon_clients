---
slug: nicolium
generated_at: 2026-08-29T00:00:00Z
prompt_version: 1
model: claude-opus-5
client_hash: seed
source_hash: none
---

<!-- section: summary -->

Nicolium is a fediverse web client forked from Soapbox, with a WYSIWYG composer,
emoji reactions, chats, groups, and per-post interaction policies. It targets
Mastodon-compatible servers broadly, with documented attention to Pleroma,
Akkoma, Iceshrimp.NET, GoToSocial, and Mitra.

<!-- section: who_is_it_for -->

People writing at length, and people on servers that are not Mastodon itself.

The WYSIWYG composer and draft handling are aimed at composition rather than
reading, and the interaction policies are of most use to someone who cares about
who can reply to what. The breadth of backend support matters if your account is
on Akkoma, GoToSocial, or Iceshrimp, where a Mastodon-only client may handle
server-specific features poorly or not at all.

Unlike its Soapbox parent, this is usable as a standalone client: there is a
public deployment, and no need to run a server to try it.

<!-- section: notable_features -->

The WYSIWYG composer is the clearest departure from the rest of this directory,
where composition is usually a plain text box. Drafts, scheduled posts, quote
posts, and post editing are all supported.

Emoji reactions, chats, and interaction policies are features of the wider
fediverse rather than of Mastodon specifically, which is consistent with the
client's stated aim of serving several backends rather than one.

Automatic language detection and URL cleaning — stripping tracking parameters
from pasted links — are both unusual enough to be worth naming.

Reading the source rather than the marketing settles the rest: multi-account
handling, push notifications, keyboard navigation, hashtag following, account
notes, notification filtering, a column layout, a service worker, and a
reduced-motion setting are all present, alongside 332 aria- attributes across the
component tree. The only core capability absent is saved searches.

<!-- section: deployment -->

A public deployment runs at web.nicolium.app, usable against any
Mastodon-compatible server with an account you already have. The client can also
be self-hosted, and the project documents installation alongside Pleroma,
Akkoma, Iceshrimp.NET, and Mitra as well as standalone.

<!-- section: source_and_licensing -->

Open source under AGPL-3.0-or-later, hosted on the Pleroma GitLab instance. The
project describes itself as a fork of Soapbox that inherits code from Mastodon,
which is consistent with the licence.

<!-- section: funding -->

No funding model beyond volunteer effort is recorded.

<!-- section: maintenance -->

Recorded as actively maintained: a commit was observed on the day this entry was
written, against a repository with a long history and no archive flag.

<!-- section: support -->

Issues are handled on the project's GitLab. No separate support channel or
documentation site is recorded here beyond the installation guides in the
repository.

<!-- section: verdict -->

The most composition-focused client in this directory, and the one that most
clearly expects your server might not be Mastodon. That breadth is the trade-off:
features built for Akkoma or Iceshrimp will do nothing on a plain Mastodon
account, and a reader who only wants to read a timeline is carrying an editor
they will not use.
