"""Daily snapshots kept in a JSON file committed alongside the cards.

Replaces the old daily_snapshots table: git is the database. One entry
per UTC day; re-running on the same day overwrites that day's entry, so
the file grows by at most one row per day however often the Action runs.
"""

import json
from pathlib import Path

from app.stats.models import UserStats

VERSION = 1


def snapshot(stats: UserStats) -> dict:
    return {
        "date": stats.fetched_at.date().isoformat(),
        "total_commits": stats.total_commits,
        "total_pull_requests": stats.total_pull_requests,
        "total_issues": stats.total_issues,
        "total_reviews": stats.total_reviews,
        "contribution_count": stats.contribution_count,
        "current_streak": stats.current_streak,
        "longest_streak": stats.longest_streak,
        "repository_count": stats.repository_count,
        "star_count": stats.star_count,
        "followers": stats.followers,
    }


def update_history(path: Path, stats: UserStats) -> bool:
    """Record today's snapshot in the history file. Returns whether the
    file changed."""
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    snapshots: list[dict] = json.loads(existing)["snapshots"] if existing else []

    today = snapshot(stats)
    by_date = {s["date"]: s for s in snapshots}
    by_date[today["date"]] = today

    content = (
        json.dumps(
            {
                "version": VERSION,
                "username": stats.username,
                "snapshots": [by_date[d] for d in sorted(by_date)],
            },
            indent=2,
        )
        + "\n"
    )
    if content == existing:
        return False
    path.write_text(content, encoding="utf-8")
    return True
