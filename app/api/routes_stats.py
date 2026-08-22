"""Statistics API endpoints."""

from datetime import date, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db.connection import get_db
from app.db.repositories import (
    LanguageRepository,
    SnapshotRepository,
    SyncStateRepository,
    UserRepository,
)
from app.stats.languages import calculate_language_percentages

router = APIRouter(prefix="/v1/users", tags=["stats"])


class StatsMetadata(BaseModel):
    """Metadata about data freshness."""

    generated_at: datetime
    last_sync: datetime | None
    sync_status: str


class UserStatsData(BaseModel):
    """User statistics data."""

    username: str
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


class UserStatsResponse(BaseModel):
    """Complete user stats response."""

    data: UserStatsData
    meta: StatsMetadata


class LanguageData(BaseModel):
    """Language statistics."""

    name: str
    bytes: int
    percentage: float


class LanguagesResponse(BaseModel):
    """Languages response."""

    data: dict[str, list[LanguageData]]
    meta: StatsMetadata


class SnapshotData(BaseModel):
    """Daily snapshot data."""

    date: date
    total_commits: int
    total_pull_requests: int
    total_issues: int
    total_reviews: int
    total_stars: int
    total_followers: int
    contribution_count: int


class HistoryResponse(BaseModel):
    """History response."""

    data: dict[str, list[SnapshotData]]
    meta: StatsMetadata


@router.get("/{username}/stats", response_model=UserStatsResponse)
def get_user_stats(username: str) -> UserStatsResponse:
    """
    Get aggregated statistics for a GitHub user.

    All statistics are precomputed and served from the database.
    This endpoint never calls the GitHub API.

    Args:
        username: GitHub username

    Returns:
        UserStatsResponse with current statistics and metadata
    """
    with get_db() as session:
        user = UserRepository.get_by_username(session, username)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {username} not found")

        sync_state = SyncStateRepository.get(session, username)

    return UserStatsResponse(
        data=UserStatsData(
            username=user.username,
            total_commits=user.total_commits,
            total_pull_requests=user.total_pull_requests,
            total_issues=user.total_issues,
            total_reviews=user.total_reviews,
            current_streak=user.current_streak,
            longest_streak=user.longest_streak,
            contribution_count=user.contribution_count,
            repository_count=user.repository_count,
            star_count=user.star_count,
            fork_count=user.fork_count,
        ),
        meta=StatsMetadata(
            generated_at=datetime.now(),
            last_sync=sync_state.last_success_at if sync_state else None,
            sync_status=sync_state.status if sync_state else "unknown",
        ),
    )


@router.get("/{username}/languages", response_model=LanguagesResponse)
def get_user_languages(username: str) -> LanguagesResponse:
    """
    Get language distribution for a GitHub user.

    Languages are aggregated from all user repositories and
    percentages are calculated based on byte counts.

    Args:
        username: GitHub username

    Returns:
        LanguagesResponse with language statistics
    """
    with get_db() as session:
        # Verify user exists
        user = UserRepository.get_by_username(session, username)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {username} not found")

        # Get language totals
        language_totals = LanguageRepository.get_all_for_user(session, username)
        sync_state = SyncStateRepository.get(session, username)

    # Calculate percentages
    lang_data = [
        (lang.language, lang.byte_count) for lang in language_totals
    ]
    percentages = calculate_language_percentages(lang_data)

    languages = [
        LanguageData(name=lang.name, bytes=lang.bytes, percentage=lang.percentage)
        for lang in percentages
    ]

    return LanguagesResponse(
        data={"languages": languages},
        meta=StatsMetadata(
            generated_at=datetime.now(),
            last_sync=sync_state.last_success_at if sync_state else None,
            sync_status=sync_state.status if sync_state else "unknown",
        ),
    )


@router.get("/{username}/history", response_model=HistoryResponse)
def get_user_history(
    username: str,
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
) -> HistoryResponse:
    """
    Get historical daily snapshots for a GitHub user.

    Defaults to last 30 days if no date range specified.
    Maximum range is 365 days.

    Args:
        username: GitHub username
        from_date: Start date (inclusive)
        to_date: End date (inclusive)

    Returns:
        HistoryResponse with daily snapshots
    """
    # Default to last 30 days
    to_date = to_date or date.today()
    from_date = from_date or (to_date - timedelta(days=30))

    # Limit range to 365 days
    if (to_date - from_date).days > 365:
        raise HTTPException(
            status_code=400,
            detail="Date range cannot exceed 365 days",
        )

    with get_db() as session:
        # Verify user exists
        user = UserRepository.get_by_username(session, username)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {username} not found")

        snapshots = SnapshotRepository.get_range(session, username, from_date, to_date)
        sync_state = SyncStateRepository.get(session, username)

    snapshot_data = [
        SnapshotData(
            date=snap.date,
            total_commits=snap.total_commits,
            total_pull_requests=snap.total_pull_requests,
            total_issues=snap.total_issues,
            total_reviews=snap.total_reviews,
            total_stars=snap.total_stars,
            total_followers=snap.total_followers,
            contribution_count=snap.contribution_count,
        )
        for snap in snapshots
    ]

    return HistoryResponse(
        data={"snapshots": snapshot_data},
        meta=StatsMetadata(
            generated_at=datetime.now(),
            last_sync=sync_state.last_success_at if sync_state else None,
            sync_status=sync_state.status if sync_state else "unknown",
        ),
    )
