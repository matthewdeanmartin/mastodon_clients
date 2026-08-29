prompt_version: 1

# Refresh an existing client review for the Mastodon Web Clients directory

An existing review is being regenerated because the client's structured facts or
its machine observations have changed. You are given the current facts, the
existing generated prose, and any human editorial overrides.

Everything in `prompts/client-review.md` applies here in full — the hard rules,
the voice, and the section list are identical. What follows is what is different
about a refresh.

## Revise; do not rewrite

The existing prose was reviewed by a human. Treat it as a good draft that needs
updating rather than as a first attempt to improve on.

- Where the facts have not changed, keep the existing wording. A refresh that
  rewrites unchanged sections produces a large diff carrying no information, and
  makes it hard to see what actually changed.
- Where the facts have changed, revise the affected sentences and leave the rest.
- Where the existing prose says something the current facts no longer support,
  fix it. That is the point of the exercise.

## Human overrides are read-only

Sections marked as human editorial overrides are shown to you for one reason:
so the sections you do write do not contradict them.

You must not reproduce them, revise them, comment on them, or write a version of
them. Anything you emit for an overridden section is discarded at build time,
and the override file is never written by this process. Attempting it wastes
your output and changes nothing.

If an override states something your other sections would contradict, defer to
the override. The editor knows something you do not.

## Changed observations are not a reason to rewrite prose

Machine observations refresh far more often than reviews do. A new commit date
or a changed HTTP status is not by itself a reason to rewrite the maintenance
section — update the specifics if the section names them, and leave the rest.

Above all: a changed signal does not license a changed conclusion. If the
computed maintenance status moved, report the new status. If it did not, do not
imply movement because an underlying number shifted.
