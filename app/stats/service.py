"""Live stats: fetch from GitHub, aggregate, and cache in-process.

There is no database. Freshness and resilience come from three layers:

1. The CDN caches every card (see the Cache-Control headers in the API),
   and keeps serving the previous copy while it revalidates.
2. This module keeps a per-instance cache, so a warm instance answers
   without touching GitHub.
3. When GitHub fails, the last good result is served (up to
   settings.stale_ttl_seconds old) instead of an error.
"""

import asyncio
import logging
import time
from datetime import UTC, date, datetime

from app.config import settings
from app.exceptions import GithubApiError, GithubNotFoundError
from app.github.client import GithubClient
from app.github.models import GithubUser
from app.stats.languages import calculate_language_percentages
from app.stats.models import LanguageShare, UserStats
from app.stats.streaks import calculate_streaks

logger = logging.getLogger(__name__)


def build_stats(user: GithubUser, fetched_at: datetime | None = None) -> UserStats:
    """Turn a raw GitHub response into card-ready stats. Pure function."""
    cc = user.contributions_collection
    calendar = cc.contribution_calendar

    contributions = [
        (date.fromisoformat(day.date), day.contribution_count)
        for week in calendar.weeks
        for day in week.contribution_days
    ]
    current_streak, longest_streak = calculate_streaks(contributions)

    repos = user.repositories.nodes
    language_bytes: dict[str, int] = {}
    language_colors: dict[str, str | None] = {}
    for repo in repos:
        if repo.is_fork or not repo.languages:
            continue
        for edge in repo.languages.edges:
            language_bytes[edge.node.name] = language_bytes.get(edge.node.name, 0) + edge.size
            language_colors[edge.node.name] = edge.node.color

    languages = [
        LanguageShare(lang.name, lang.bytes, lang.percentage, language_colors.get(lang.name))
        for lang in calculate_language_percentages(list(language_bytes.items()))
    ]

    return UserStats(
        username=user.login,
        name=user.name,
        followers=user.followers.total_count,
        total_commits=cc.total_commit_contributions,
        total_pull_requests=cc.total_pull_request_contributions,
        total_issues=cc.total_issue_contributions,
        total_reviews=cc.total_pull_request_review_contributions,
        current_streak=current_streak,
        longest_streak=longest_streak,
        contribution_count=calendar.total_contributions,
        repository_count=user.repositories.total_count,
        star_count=sum(r.stargazer_count for r in repos),
        fork_count=sum(r.fork_count for r in repos),
        languages=languages,
        fetched_at=fetched_at or datetime.now(UTC),
    )


# username (lowercased) -> (monotonic time stored, stats)
_cache: dict[str, tuple[float, UserStats]] = {}


def _cache_put(key: str, stats: UserStats) -> None:
    _cache.pop(key, None)
    _cache[key] = (time.monotonic(), stats)
    while len(_cache) > settings.cache_max_entries:
        _cache.pop(next(iter(_cache)))  # dicts keep insertion order: drop oldest


def clear_cache() -> None:
    _cache.clear()


async def get_user_stats(username: str, client: GithubClient | None = None) -> UserStats:
    """Return stats for a user, from cache when fresh.

    Raises:
        GithubNotFoundError: the user does not exist.
        GithubApiError: GitHub failed and there is no usable stale copy.
    """
    key = username.lower()
    cached = _cache.get(key)
    age = time.monotonic() - cached[0] if cached else None

    if cached and age is not None and age < settings.cache_ttl_seconds:
        return cached[1]

    try:
        user = await asyncio.wait_for(
            (client or GithubClient()).fetch_user(username),
            # One budget for the whole fetch, pagination included.
            timeout=settings.github_timeout_seconds + 1,
        )
    except GithubNotFoundError:
        _cache.pop(key, None)
        raise
    except (GithubApiError, TimeoutError) as e:
        if cached and age is not None and age < settings.stale_ttl_seconds:
            logger.warning(f"GitHub fetch for {username} failed ({e}); serving stale copy")
            return cached[1]
        if isinstance(e, TimeoutError):
            raise GithubApiError("GitHub did not respond in time") from e
        raise

    stats = build_stats(user)
    _cache_put(key, stats)
    return stats
