"""Aggregate metrics calculation."""

from datetime import date
from typing import NamedTuple

from app.db.models import DailySnapshot, User


class UserAggregates(NamedTuple):
    """Computed user aggregates."""

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


def compute_user_aggregates(
    github_totals: dict,
    current_streak: int,
    longest_streak: int,
    contribution_count: int,
    repo_count: int,
    total_stars: int,
    total_forks: int,
) -> UserAggregates:
    """
    Compute final user aggregates from various sources.

    Args:
        github_totals: Dict with totalCommitContributions, etc. from GitHub API
        current_streak: Calculated current streak
        longest_streak: Calculated longest streak
        contribution_count: Sum of contribution calendar
        repo_count: Number of repositories
        total_stars: Total stars across repos
        total_forks: Total forks across repos

    Returns:
        UserAggregates with all computed values
    """
    return UserAggregates(
        total_commits=github_totals.get("totalCommitContributions", 0),
        total_pull_requests=github_totals.get("totalPullRequestContributions", 0),
        total_issues=github_totals.get("totalIssueContributions", 0),
        total_reviews=github_totals.get("totalPullRequestReviewContributions", 0),
        current_streak=current_streak,
        longest_streak=longest_streak,
        contribution_count=contribution_count,
        repository_count=repo_count,
        star_count=total_stars,
        fork_count=total_forks,
    )


def create_daily_snapshot(username: str, user: User, followers: int) -> DailySnapshot:
    """
    Create a daily snapshot from current user stats.

    Args:
        username: GitHub username
        user: User model with current stats
        followers: Current follower count

    Returns:
        DailySnapshot for today
    """
    return DailySnapshot(
        username=username,
        date=date.today(),
        total_commits=user.total_commits,
        total_pull_requests=user.total_pull_requests,
        total_issues=user.total_issues,
        total_reviews=user.total_reviews,
        total_stars=user.star_count,
        total_followers=followers,
        contribution_count=user.contribution_count,
    )
