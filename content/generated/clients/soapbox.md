---
slug: soapbox
generated_at: 2026-08-29T00:00:00Z
prompt_version: 1
model: claude-opus-5
client_hash: seed
source_hash: none
---

<!-- section: summary -->

Soapbox is an alternative fediverse frontend, built to be deployed by a server
operator in place of the stock interface rather than opened as a standalone
client. A public deployment exists at fe.soapbox.pub for anyone who wants to try
it against their own account.

<!-- section: who_is_it_for -->

Primarily server operators. If you run a Mastodon-compatible instance and want
it to look and behave differently from stock, Soapbox is designed for exactly
that, with custom branding as a stated goal.

For an individual reader who just wants a nicer client, it is a less natural
fit. The deployment you use is chosen by whoever runs your server, not by you.

<!-- section: notable_features -->

Quote posts and scheduled posts, both absent from several clients here. Lists,
filters, bookmarks, polls, and a column layout are supported.

Several capabilities are recorded as unknown: multi-account handling, push
notifications, keyboard navigation, and accessibility work were not established
from the available material, and are marked unknown rather than assumed.

<!-- section: deployment -->

Soapbox is deployed alongside a server rather than used as an independent
frontend against an arbitrary instance. Using it in the way it was designed for
means operating the server side too.

The public deployment at fe.soapbox.pub is the exception: it is a running
instance of the frontend you can point at your own account without deploying
anything.

<!-- section: source_and_licensing -->

Open source under AGPL-3.0. The primary repository is on GitLab, with a GitHub
mirror.

<!-- section: funding -->

Donations and volunteer effort.

<!-- section: maintenance -->

Recorded as actively maintained. A commit was observed within the last week, and
the repository is not archived.

<!-- section: support -->

An issue tracker on the GitLab repository. No separate documentation site or
support channel is recorded here.

<!-- section: verdict -->

A frontend for people running servers, not a client for people using them. If
you operate an instance and want control over how it presents itself, that is
what this is built for; if you are looking for something to open and log into,
the public deployment will show you what it is like, but the product is aimed
past you.
