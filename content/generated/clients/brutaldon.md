---
slug: brutaldon
generated_at: 2026-08-29T00:00:00Z
prompt_version: 1
model: claude-opus-5
client_hash: seed
source_hash: none
---

<!-- section: summary -->

Brutaldon is a deliberately plain web interface for Mastodon and Pleroma,
written as a Django application and rendered as ordinary HTML. It works entirely
without JavaScript, including in text-mode browsers such as Lynx, w3m, and
elinks; where JavaScript is available it is used to enhance rather than to
enable.

<!-- section: who_is_it_for -->

Anyone whose browser, connection, or assistive technology does badly with a
JavaScript application. That covers text-mode browsers, very old hardware,
scripting turned off by policy, and screen-reader setups that fare better with
plain semantic HTML than with a scripted interface.

It is also a reasonable answer for someone who simply wants Mastodon to be a
website rather than an application.

It is not a fit for anyone who wants lists, bookmarks, or a rich composer. Those
are not incidental gaps: the project has chosen a set of constraints, and the
missing features are the price of them.

<!-- section: notable_features -->

Working without JavaScript at all is the feature. Nothing else in this directory
does it, and it is what makes Brutaldon usable in places where the rest are not.

The underlying client is more capable than its plainness suggests: multi-account
switching, filters, polls, post editing via redraft, follow requests, blocking
and muting, custom emoji, and content warnings are all present in the routes.

The absences are real and worth naming. There are no lists, no bookmarks, no
profile editing, no hashtag following, no scheduled posts, and no translation.

One correction to the project's own documentation: the README says filters are
missing. They are not — the source has routes for creating, listing, editing,
and deleting them. The README appears to be out of date, and this directory
records what the code does.

<!-- section: deployment -->

A public deployment runs at brutaldon.org, which you can log into with an account
on any Mastodon-compatible server. The project actively encourages running your
own instead, either locally or on a public server.

Note that Brutaldon is a server-side application rather than a page that runs in
your browser: self-hosting it means running a Django app, not serving static
files.

<!-- section: source_and_licensing -->

Open source under AGPL-3.0-or-later. The primary repository is on GitLab; a
GitHub mirror exists but the README warns it may lag.

The issue tracker is not readable without signing in to GitLab, so this
directory records no link to it.

<!-- section: funding -->

Volunteer effort. No funding page is recorded.

<!-- section: maintenance -->

The most recent commit in the source is from November 2024, with repository
activity recorded into late 2025. The repository is not archived and the hosted
instance responds.

That pace suits what the project is. A client with a deliberately fixed feature
set and no framework to chase has less reason to change than one tracking a
moving target, and a quiet repository here is weaker evidence of neglect than it
would be elsewhere.

<!-- section: support -->

Little is recorded. The issue tracker exists but requires a GitLab account to
read, and no separate documentation site or support channel was found beyond the
README and INSTALL notes in the repository.

<!-- section: verdict -->

The client to reach for when the others will not run. Brutaldon trades away
lists, bookmarks, profile editing, and a modern composer, and in exchange works
in a text browser over a bad connection with scripting disabled. For a reader
who does not need that, the trade is a poor one; for a reader who does, nothing
else in this directory is a substitute.
