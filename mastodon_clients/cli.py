"""Command-line entry point.

Subcommands map one-to-one onto Makefile targets (spec 23). Only
`refresh-metadata` and the review generators touch the network or an LLM, and
neither is part of `build` (invariants 1 and 2).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from mastodon_clients.errors import ValidationError
from mastodon_clients.repository import Site, load_site, unpublished_reason


def _root(args: argparse.Namespace) -> Path:
    return Path(args.root).resolve()


def _load(args: argparse.Namespace) -> Site:
    return load_site(_root(args))


def _fail_on_issues(site: Site) -> None:
    """A validation failure stops the build (spec 24)."""
    if not site.report.ok:
        raise ValidationError(site.report)


def cmd_validate(args: argparse.Namespace) -> int:
    site = _load(args)
    if not site.report.ok:
        count = len(site.report.issues)
        print(f"{count} validation issue{'s' if count != 1 else ''}:", file=sys.stderr)
        print(site.report.render(), file=sys.stderr)
        return 1

    print(f"{len(site.clients)} client record{'s' if len(site.clients) != 1 else ''} valid.")
    for client in site.clients:
        reason = unpublished_reason(client)
        if reason:
            print(f"  {client.slug}: not published ({reason})")
    warnings = site.warnings
    if warnings:
        print(f"\n{len(warnings)} health warning{'s' if len(warnings) != 1 else ''} for review:")
        for warning in warnings:
            print(f"  {warning.client}: {warning.message}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    site = _load(args)
    _fail_on_issues(site)
    width = max((len(c.name) for c in site.listed), default=0)
    for client in site.listed:
        score = site.scores[client.slug]
        note = f"  ({score.unknown_features} unknown features)" if score.unknown_features else ""
        print(f"{client.name:<{width}}  {score.stars:>3} stars  {score.points:5.1f}/100  {site.status_of(client.slug)}{note}")
    return 0


def cmd_build_content(args: argparse.Namespace) -> int:
    # Imported here rather than at module scope so `validate` and `score` do not
    # pay for the content builder's imports.
    from mastodon_clients.build_content import build_content

    site = _load(args)
    _fail_on_issues(site)
    written = build_content(site)
    print(f"Wrote {written} content file{'s' if written != 1 else ''}.")
    return 0


def cmd_sitemap(args: argparse.Namespace) -> int:
    from mastodon_clients.sitemap import check_local_assets, write_robots, write_sitemap

    output = Path(args.output).resolve()
    if not output.is_dir():
        print(f"{output} does not exist; run the Pelican build first.", file=sys.stderr)
        return 1
    missing = check_local_assets(output, args.site_url)
    if missing:
        print("Pages reference assets that were not built:", file=sys.stderr)
        for path in missing:
            print(f"  {path}", file=sys.stderr)
        return 1

    count = write_sitemap(output, args.site_url)
    write_robots(output, args.site_url)
    print(f"Wrote sitemap.xml with {count} URLs, and robots.txt.")
    return 0


def cmd_generate_review(args: argparse.Namespace) -> int:
    from mastodon_clients.generate import generate_review

    site = _load(args)
    _fail_on_issues(site)
    return generate_review(site, slug=args.client, refresh=args.refresh, model=args.model)


def cmd_refresh_metadata(args: argparse.Namespace) -> int:
    # The only subcommand permitted to reach the network, and the only one that
    # imports the collector at all (invariant 1).
    from mastodon_clients.collect import refresh_metadata

    site = _load(args)
    return refresh_metadata(site, only=args.client, timeout=args.timeout)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mastodon_clients", description=__doc__)
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate every data file")
    validate.set_defaults(func=cmd_validate)

    score = subparsers.add_parser("score", help="print the computed ratings")
    score.set_defaults(func=cmd_score)

    build = subparsers.add_parser("build-content", help="assemble Pelican content from data")
    build.set_defaults(func=cmd_build_content)

    sitemap = subparsers.add_parser("sitemap", help="write sitemap.xml and robots.txt into the built site")
    sitemap.add_argument("--output", default="output", help="the Pelican output directory")
    sitemap.add_argument("--site-url", default="https://matthewdeanmartin.github.io/mastodon_clients", help="absolute site URL")
    sitemap.set_defaults(func=cmd_sitemap)

    generate = subparsers.add_parser("generate-review", help="generate prose for exactly one client")
    generate.add_argument("client", help="client slug")
    generate.add_argument("--refresh", action="store_true", help="use the refresh prompt and existing prose")
    generate.add_argument("--model", default="claude-opus-5", help="model identifier recorded in provenance")
    generate.set_defaults(func=cmd_generate_review)

    refresh = subparsers.add_parser("refresh-metadata", help="collect machine observations (network access)")
    refresh.add_argument("--client", default=None, help="limit collection to one slug")
    refresh.add_argument("--timeout", type=float, default=10.0, help="per-request timeout in seconds")
    refresh.set_defaults(func=cmd_refresh_metadata)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = args.func(args)
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return int(result)


if __name__ == "__main__":
    raise SystemExit(main())
