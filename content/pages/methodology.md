Title: Methodology
Slug: methodology
URL: methodology/
Save_as: methodology/index.html
Template: page
Description: What qualifies as a client, how features and maintenance are assessed, how ratings are calculated, and how this site's commercial interest is handled.

This page sets out the rules this site follows. Writing them down is partly for
your benefit and partly for the editor's: rules that are only in someone's head
drift, and a directory that drifts is worse than useless.

## What counts as a client

A product is included when all three of these hold:

1. it talks to servers over the Mastodon-compatible REST API;
2. it is primarily for reading, browsing, posting to, and otherwise interacting
   with Mastodon-style feeds;
3. it is usable through the web.

That covers standalone hosted clients, self-hostable clients, alternative
Mastodon frontends, and clients that ship as part of another
Mastodon-compatible server.

Whether the same project also has an Android, iOS, macOS, Windows, or Linux
application is irrelevant here. This directory is about the web client.

## What is excluded

Software whose purpose is a narrow, one-off Mastodon task rather than general
feed interaction is out of scope, including:

- account migration utilities;
- bulk preference-changing tools;
- bulk follow and unfollow tools;
- correlation and discovery utilities, such as tools for finding Twitter
  contacts on Mastodon;
- single-purpose moderation utilities;
- analytics-only applications;
- command-line scripts that do not function as a general client.

The line is "could you use this as your everyday client?" A tool that does one
thing well and is not meant to be lived in does not belong here, however good it
is at that thing.

When a known product is deliberately judged out of scope, that decision is
recorded in the repository rather than left implicit, so the same question does
not get answered differently next year.

## Forks and families

Fediverse clients get forked a lot, and a fork is usually the same software with
a different maintainer. Pinafore, Semaphore, and Enafore are one lineage;
listing them as three peers would tell you to "use Pinafore, or Pinafore, or
Pinafore", which is noise rather than choice.

So the directory shows **one row per family**. A fork keeps its own page and its
own permanent URL, and appears in the machine-readable data like any other
record, but it does not occupy a row of its own in the table.

The family's row reports the **best** maintenance status in the family, not the
parent's. A project whose original author stopped but whose fork is thriving is
not a dead project, and reporting it as one would push you away from working
software.

Each parent's page carries a Forks section comparing the family. What usually
differs between forks is which one is still being maintained, so that is the
first column.

Where a discontinued client has a maintained fork, the dead client's page leads
with a link to the living one. You arrived looking for something that works.

## How features are assessed

Each client has a structured record listing every feature in the site's
taxonomy. A feature can be:

- **Yes** &mdash; supported;
- **No** &mdash; not supported;
- **Partial** &mdash; supported in a limited or incomplete way;
- **Unknown** &mdash; we have not established the answer;
- **Not applicable** &mdash; the feature cannot meaningfully apply to this client.

**"Partial" involves judgement.** Keyboard navigation is the clearest example: a
client may handle a handful of shortcuts or may be fully operable without a
mouse, and both get described as "keyboard support" by their authors. Where a
call has been made, the individual review says what the limitation is.

**"Unknown" is used freely and deliberately.** It is better to record that we do
not know than to guess. The cost is real, though: unknown values earn no points
in the rating, so an under-researched client scores lower than it should. To
keep that from being invisible, the number of unknown core features is shown
next to every rating. A correction that turns an unknown into a fact is the most
valuable thing you can send.

**Some features depend on the server.** Post editing, scheduled posts, and quote
posts are server capabilities that a client may or may not expose. Where a
client's support is limited by the server rather than by the client, the review
says so.

## How ratings are calculated

Ratings are computed by code from the structured records. No editor assigns one,
and no language model contributes to one. Given the same data, anyone with the
repository gets the same numbers.

[The complete formula, generated from the scoring code
itself](/methodology/scoring/), including how unknown values are handled and why
half-star granularity is the limit.

The short version: five components &mdash; feature breadth, maintenance signals,
deployment and documentation, support resources, and accessibility &mdash;
totalling 100 points, converted to stars.

A single number cannot capture what different readers need. The directory is
ordered by rating because a reader opening a list of clients is usually asking
which to use, and making them scroll alphabetically to find out serves neutrality
at their expense. But the ordering is a starting point, not a verdict: the
audience pages and the directory filters answer "which one for me?" far better
than a ranking answers "which is best?"

## How maintenance is assessed

Maintenance is not one metric, and this site does not treat it as one.

Several independent signals are collected:

- the latest source commit;
- the latest release or tag;
- whether the repository is archived;
- whether the homepage responds;
- whether the hosted application responds;
- whether the documentation is reachable;
- whether the source repository still exists;
- domain resolution and certificate validity;
- any explicit announcement of discontinuation.

These are synthesised into one of: actively maintained, maintained, low
activity, possibly unmaintained, unmaintained, discontinued, or unknown. The
derivation is deterministic, and the raw observations are shown on each client's
page so you can see what the status rests on.

### Why no single signal is decisive

Each of these signals fails in a way that looks like abandonment but is not:

- A **dead domain** may be a lapsed registration, a DNS problem, or a move.
- **No commits for six months** may mean a project is finished rather than
  abandoned. Some software stops changing because it works.
- **An archived repository** may mean development moved elsewhere.
- **A hosted instance being down** says nothing about the software.

So no single signal can move a client to "unmaintained", and nothing except an
explicit editorial decision, backed by recorded evidence, can move one to
"discontinued". Long inactivity with no corroboration reaches "possibly
unmaintained" and stops there.

Conditions worth attention are raised as **warnings for a human to look at**,
never as automatic conclusions.

### Editorial links and observed state are separate

A link recorded for a client is not deleted or rewritten because a check failed.
The recorded URL stays, and the last observed result sits beside it:

> Known homepage: `https://example.com/`
> Last check: 503 Service Unavailable on 2026-08-29

A temporary outage should not erase a fact.

## Two dates, not one

Every client page shows two different things:

- **Review last updated** &mdash; when a human last read and revised the review;
- **Automated project signals checked** &mdash; when the machine observations
  were last collected.

Machine signals can be much fresher than the prose around them. A recent signal
check does not mean anyone has re-read the client.

## How the data is maintained

Facts live in one file per client in a
[public repository](https://github.com/matthewdeanmartin/mastodon_clients).
Prose sits on top of the structured data rather than hiding facts inside
narrative.

Machine observations are collected by an explicitly run job, not on a schedule
and never during a site build. The site builds from committed data with no
network access at all, which means the pages you are reading are reproducible
from a commit.

Draft prose may be generated with the assistance of a language model, always
from the structured facts and never as an authority over them. A language model
never assigns a rating, never establishes a fact, and never rewrites text a
human has edited.

## About the author

Created by Matthew Martin, creator of Mawkingbird, a Mastodon client for new users and power users. [About this guide](/about/).

## Corrections

[How to send one](/submit/).
