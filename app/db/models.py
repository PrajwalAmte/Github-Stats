from datetime import date, datetime

from pydantic import BaseModel


class User(BaseModel):
    """User profile and aggregated statistics."""

    username: str
    name: str | None = None
    avatar_url: str | None = None
    followers: int = 0
    following: int = 0
    public_repos: int = 0
    public_gists: int = 0
    total_commits: int = 0
    total_pull_requests: int = 0
    total_issues: int = 0
    total_reviews: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    contribution_count: int = 0
    repository_count: int = 0
    fork_count: int = 0
    star_count: int = 0
    stats_computed_at: datetime | None = None
    updated_at: datetime | None = None


class Repository(BaseModel):
    """GitHub repository metadata."""

    github_id: int
    owner: str
    name: str
    stars: int = 0
    forks: int = 0
    primary_language: str | None = None
    is_fork: bool = False
    pushed_at: datetime | None = None
    synced_at: datetime | None = None


class ContributionDay(BaseModel):
    """Daily contribution count from GitHub contribution calendar."""

    username: str
    date: date
    count: int


class LanguageTotal(BaseModel):
    """Language byte counts per user."""

    username: str
    language: str
    byte_count: int
    updated_at: datetime | None = None


class DailySnapshot(BaseModel):
    """Historical daily snapshot of user statistics."""

    username: str
    date: date
    total_commits: int
    total_pull_requests: int
    total_issues: int
    total_reviews: int
    total_stars: int
    total_followers: int
    contribution_count: int


class SyncState(BaseModel):
    """Synchronization state and locking metadata."""

    username: str
    locked_until: datetime | None = None
    lock_token: str | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    consecutive_failures: int = 0
    status: str = "ok"  # ok | degraded | failing
    last_error: str | None = None
    updated_at: datetime | None = None
