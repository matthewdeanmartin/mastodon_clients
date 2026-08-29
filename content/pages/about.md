Title: About Mawkingbird
Slug: about
URL: about/
Save_as: about/index.html
Template: page
Description: Who runs this site, the commercial interest behind it, and the editorial approach that follows from both.

## Who runs this

This site is written and operated by **Matthew Martin**.

## The conflict of interest

Matthew Martin also maintains **Mawkingbird**, a freemium Mastodon web client,
at [mawkingbird.com](https://mawkingbird.com/).

That means the person writing these reviews sells a product in the category
being reviewed. Every client listed here is, to some degree, a competitor.

This is not a footnote and there is no framing that makes it disappear. It is
the single most important thing to know when reading anything on this site, and
it should shape how much weight you give what you find here.

### What is done about it

The honest answer is that disclosure alone does not neutralise a conflict of
interest. What follows are structural choices that make the bias easier for you
to check, not claims that it has been eliminated.

**Facts are separated from opinion.** Every claim about what a client does lives
in a structured record in a
[public repository](https://github.com/matthewdeanmartin/mastodon_clients), not
inside prose. You can read the record for a client and see exactly what was
asserted about it, without reading around an adjective.

**Ratings are computed, not assigned.** The star ratings come from code applied
to those records. The editor cannot lower a competitor's score without changing
a recorded fact, and changing a recorded fact leaves a diff in public version
control. [The formula is published in full](/methodology/scoring/).

**Corrections are cheap and public.** A correction is a change to one small
file. Submitting one does not require going through the editor's judgement about
whether the prose reads fairly &mdash; it requires pointing at a wrong value.

**What is not claimed.** There is no independent review board, no second editor,
and no audit. Feature assessments involve judgement about what counts as
"partial" support, and that judgement is the editor's. If you think a call was
made in a self-serving direction, the underlying data is there for you to check,
and [saying so](/submit/) is welcome.

## Editorial approach

The voice here is deliberately restrained.

**Facts are distinguished from interpretation.** A review says what a client
does, then separately says what we make of it. Where those blur, that is a
defect in the writing, and worth reporting.

**Popularity is not quality.** A client with more users is a client with more
users. It may also be better; that has to be argued from what it does, not from
how many people use it.

**Age is neither a virtue nor a fault.** A mature client that has stopped
changing may be finished rather than abandoned. A new one may be promising or
may be a weekend project. Both readings require evidence.

**Uncertainty is stated, not smoothed over.** Where a fact has not been
established, pages say "unknown" rather than guessing. This has a real cost:
unknown values earn no rating points, so a little-researched client scores lower
than it might deserve. The count of unknowns is therefore shown next to every
rating, so you can tell a genuinely limited client from an under-researched one.

**No client is called dead on one signal.** A homepage that returns an error, a
repository with no commits this quarter, an expired certificate &mdash; none of
these, alone, means a project has ended. Several independent signals are
collected, and the synthesis is deliberately reluctant.
[How that works](/methodology/).

## What is and is not covered

This directory covers **web clients** for Mastodon-compatible servers: software
you use through a browser to read, browse, and post to Mastodon-style feeds.

It does not cover native mobile or desktop applications, general Fediverse
software, or single-purpose Mastodon utilities such as account migration tools
or bulk unfollow scripts. Whether a client also has a native app elsewhere is
not what is being assessed.

The [methodology page](/methodology/) sets out the inclusion rules in detail, so
that decisions about borderline products stay consistent over time.

## Corrections and suggestions

[How to send one](/submit/). Corrections that resolve an "unknown" are the most
useful kind.
