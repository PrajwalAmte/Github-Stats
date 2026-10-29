"""Statistics API endpoints."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from app.api.common import CACHE_OK, is_valid_username
from app.exceptions import GithubApiError, GithubNotFoundError
from app.stats.models import UserStats
from app.stats.service import get_user_stats

router = APIRouter(prefix="/v1/users", tags=["stats"])


class StatsMetadata(BaseModel):
    """Metadata about data freshness."""

    fetched_at: datetime


class UserStatsData(BaseModel):
    """User statistics data."""

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


class UserStatsResponse(BaseModel):
    """Complete user stats response."""

    data: UserStatsData
    meta: StatsMetadata


class LanguageData(BaseModel):
    """Language statistics."""

    name: str
    bytes: int
    percentage: float
    color: str | None


class LanguagesResponse(BaseModel):
    """Languages response."""

    data: dict[str, list[LanguageData]]
    meta: StatsMetadata


async def _load(username: str, response: Response) -> UserStats:
    if not is_valid_username(username):
        raise HTTPException(status_code=400, detail="Invalid GitHub username")
    try:
        stats = await get_user_stats(username)
    except GithubNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"User {username} not found") from e
    except GithubApiError as e:
        raise HTTPException(status_code=503, detail="GitHub is unavailable, try again") from e
    response.headers["Cache-Control"] = CACHE_OK
    return stats


@router.get("/{username}/stats", response_model=UserStatsResponse)
async def get_user_stats_json(username: str, response: Response) -> UserStatsResponse:
    """Aggregated statistics for a GitHub user (contribution counts cover the last year)."""
    stats = await _load(username, response)
    return UserStatsResponse(
        data=UserStatsData(
            username=stats.username,
            name=stats.name,
            followers=stats.followers,
            total_commits=stats.total_commits,
            total_pull_requests=stats.total_pull_requests,
            total_issues=stats.total_issues,
            total_reviews=stats.total_reviews,
            current_streak=stats.current_streak,
            longest_streak=stats.longest_streak,
            contribution_count=stats.contribution_count,
            repository_count=stats.repository_count,
            star_count=stats.star_count,
            fork_count=stats.fork_count,
        ),
        meta=StatsMetadata(fetched_at=stats.fetched_at),
    )


@router.get("/{username}/languages", response_model=LanguagesResponse)
async def get_user_languages(username: str, response: Response) -> LanguagesResponse:
    """Language distribution across a user's non-fork repositories, by bytes."""
    stats = await _load(username, response)
    return LanguagesResponse(
        data={
            "languages": [
                LanguageData(
                    name=lang.name, bytes=lang.bytes, percentage=lang.percentage, color=lang.color
                )
                for lang in stats.languages
            ]
        },
        meta=StatsMetadata(fetched_at=stats.fetched_at),
    )
