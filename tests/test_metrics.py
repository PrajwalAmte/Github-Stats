"""Tests for metrics aggregation."""

from datetime import date

from app.db.models import User
from app.stats.metrics import compute_user_aggregates, create_daily_snapshot


def test_compute_user_aggregates():
    """Test computing user aggregates."""
    github_totals = {
        "totalCommitContributions": 1000,
        "totalPullRequestContributions": 50,
        "totalIssueContributions": 25,
        "totalPullRequestReviewContributions": 75,
    }

    aggregates = compute_user_aggregates(
        github_totals=github_totals,
        current_streak=10,
        longest_streak=25,
        contribution_count=500,
        repo_count=15,
        total_stars=100,
        total_forks=20,
    )

    assert aggregates.total_commits == 1000
    assert aggregates.total_pull_requests == 50
    assert aggregates.total_issues == 25
    assert aggregates.total_reviews == 75
    assert aggregates.current_streak == 10
    assert aggregates.longest_streak == 25
    assert aggregates.contribution_count == 500
    assert aggregates.repository_count == 15
    assert aggregates.star_count == 100
    assert aggregates.fork_count == 20


def test_create_daily_snapshot():
    """Test creating a daily snapshot."""
    user = User(
        username="testuser",
        total_commits=1000,
        total_pull_requests=50,
        total_issues=25,
        total_reviews=75,
        star_count=100,
        contribution_count=500,
    )

    snapshot = create_daily_snapshot("testuser", user, 150)

    assert snapshot.username == "testuser"
    assert snapshot.date == date.today()
    assert snapshot.total_commits == 1000
    assert snapshot.total_pull_requests == 50
    assert snapshot.total_issues == 25
    assert snapshot.total_reviews == 75
    assert snapshot.total_stars == 100
    assert snapshot.total_followers == 150
    assert snapshot.contribution_count == 500
