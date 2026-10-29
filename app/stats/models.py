"""Card-ready statistics for a user."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LanguageShare:
    name: str
    bytes: int
    percentage: float
    color: str | None


@dataclass(frozen=True)
class UserStats:
    username: str
    name: str | None
    followers: int
    total_commits: int
    total_pull_requests: int
    total_issues: int
    total_reviews: int
    current_streak: int
    longest_streak: int
    contribution_count: int
    repository_count: int
    star_count: int
    fork_count: int
    languages: list[LanguageShare]
    fetched_at: datetime
