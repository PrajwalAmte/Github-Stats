"""Render cards to SVG files — used by the GitHub Action.

    python -m app.cli USERNAME --out DIR [--cards overview,profile] [--no-history]

Reads the token from GITHUB_TOKEN. The files are meant to be committed
to the user's own repo, so the README loads them from GitHub itself and
no external service is involved at view time.
"""

import argparse
import asyncio
import re
import sys
from pathlib import Path

from app.cards import CARDS
from app.config import settings
from app.exceptions import GithubApiError
from app.stats.history import update_history
from app.stats.service import get_user_stats

# The footer timestamp changes on every run. Ignore it when deciding
# whether a card changed, so a scheduled run with no new activity
# doesn't produce a commit.
_TIMESTAMP_RE = re.compile(r"# updated [^<]*")


def _same_ignoring_timestamp(a: str, b: str) -> bool:
    return _TIMESTAMP_RE.sub("", a) == _TIMESTAMP_RE.sub("", b)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description=__doc__)
    parser.add_argument("username")
    parser.add_argument("--out", default="github-stats", help="output directory")
    parser.add_argument(
        "--cards", default=",".join(CARDS), help=f"comma-separated subset of: {', '.join(CARDS)}"
    )
    parser.add_argument(
        "--no-history",
        dest="history",
        action="store_false",
        help="don't record today's snapshot in DIR/history.json",
    )
    args = parser.parse_args(argv)

    cards = [c.strip() for c in args.cards.split(",") if c.strip()]
    unknown = [c for c in cards if c not in CARDS]
    if unknown:
        parser.error(f"unknown card(s): {', '.join(unknown)}")

    # Nobody is waiting on an image here, so fetch every repo.
    settings.github_timeout_seconds = 60
    settings.github_soft_budget_seconds = 300
    settings.max_repo_pages = 50

    try:
        stats = asyncio.run(get_user_stats(args.username))
    except GithubApiError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for card in cards:
        path = out / f"{card}.svg"
        svg = CARDS[card](stats)
        if path.exists() and _same_ignoring_timestamp(path.read_text(encoding="utf-8"), svg):
            print(f"unchanged {path}")
            continue
        path.write_text(svg, encoding="utf-8")
        print(f"wrote {path}")

    if args.history:
        path = out / "history.json"
        print(f"{'wrote' if update_history(path, stats) else 'unchanged'} {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
