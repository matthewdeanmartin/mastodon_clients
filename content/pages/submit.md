Title: Suggest a client or send a correction
Slug: submit
URL: submit/
Save_as: submit/index.html
Template: page
Description: How to propose a Mastodon web client for inclusion, or correct something this site got wrong.

There is no account system here and nothing to sign up for. Two routes:

- **Open an issue** on
  [github.com/matthewdeanmartin/mastodon_clients](https://github.com/matthewdeanmartin/mastodon_clients/issues).
- **Send a message** to
  [@mistersql@mastodon.social](https://mastodon.social/@mistersql).

Either is fine. Use whichever you already have open.

## Corrections

These are the most useful thing you can send, and the easiest to act on.

Every fact on this site comes from a structured record, so a correction is a
change to one field in one file. What helps:

- which client;
- which fact is wrong;
- what it should be;
- how you know &mdash; a link, a commit, a release note, a screenshot.

That last one matters more than it might seem. This site tries not to assert
things it cannot back up, so a correction with a source can be applied
immediately, while one without needs verifying first.

### Resolving an "unknown" is especially welcome

Where a fact has not been established, pages say **unknown** rather than
guessing. Unknown values earn no rating points, which means an under-researched
client scores lower than it deserves.

If you use a client and can confirm that it does or does not do something the
directory lists as unknown, that single answer improves both its page and its
rating.

## Proposing a client

Included products are web clients for Mastodon-compatible servers: software you
use in a browser to read, browse, and post to Mastodon-style feeds.
[The inclusion rules in full](/methodology/), including what is deliberately out
of scope.

Useful things to include:

- the client's name and homepage;
- a hosted instance, if there is one;
- the source repository, if it is public;
- the licence, if you know it;
- how it is funded, if you know;
- anything unusual about it &mdash; particularly whether it can work against any
  server or needs its own backend deployed.

Anything you do not know can be left out. It gets recorded as unknown, which is
an honest starting point.

### If you maintain the client

Say so &mdash; it is useful context, not a disqualification, and you are likely
the best source for what your own software does.

What that does not change is how the client is assessed: ratings are
[computed from the structured data by code](/methodology/scoring/), so nothing
about a submission can adjust a score except the recorded facts themselves.

## If you think a review is unfair

Worth saying plainly, given [who runs this site](/about/): the editor maintains a
competing Mastodon client. If a review of your client reads as though that
influenced it, that is a fair thing to raise, and raising it publicly on the
issue tracker is entirely reasonable.

The underlying data is public, and the scoring code is public, so a claim of
unfairness is something that can actually be checked rather than argued about.
