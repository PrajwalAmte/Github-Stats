"""SVG card API endpoints."""

from fastapi import APIRouter, HTTPException, Response

from app.cards.languages import generate_languages_card
from app.cards.overview import generate_overview_card
from app.cards.profile import generate_profile_card
from app.cards.streak import generate_streak_card
from app.db.connection import get_db
from app.db.repositories import LanguageRepository, SyncStateRepository, UserRepository

router = APIRouter(prefix="/v1/users", tags=["cards"])


@router.get("/{username}/cards/profile.svg")
def get_profile_card(username: str) -> Response:
    """
    Generate and return a profile statistics SVG card.

    Args:
        username: GitHub username

    Returns:
        SVG image response with profile statistics
    """
    with get_db() as session:
        user = UserRepository.get_by_username(session, username)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {username} not found")

        sync_state = SyncStateRepository.get(session, username)

    svg_content = generate_profile_card(
        username=user.username,
        total_commits=user.total_commits,
        total_prs=user.total_pull_requests,
        total_issues=user.total_issues,
        total_reviews=user.total_reviews,
        star_count=user.star_count,
        repo_count=user.repository_count,
        current_streak=user.current_streak,
        longest_streak=user.longest_streak,
        last_sync=sync_state.last_success_at if sync_state else None,
    )

    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, s-maxage=3600, stale-while-revalidate=86400",
        },
    )


@router.get("/{username}/cards/overview.svg")
def get_overview_card(username: str) -> Response:
    """Generate and return a consolidated wide SVG card."""
    with get_db() as session:
        user = UserRepository.get_by_username(session, username)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {username} not found")

        language_totals = LanguageRepository.get_all_for_user(session, username)
        sync_state = SyncStateRepository.get(session, username)

    total_bytes = sum(lang.byte_count for lang in language_totals)
    languages = []
    if total_bytes > 0:
        languages = [
            (lang.language, (lang.byte_count / total_bytes) * 100) for lang in language_totals[:6]
        ]

    svg_content = generate_overview_card(
        username=user.username,
        total_commits=user.total_commits,
        total_prs=user.total_pull_requests,
        total_issues=user.total_issues,
        total_reviews=user.total_reviews,
        star_count=user.star_count,
        repo_count=user.repository_count,
        current_streak=user.current_streak,
        longest_streak=user.longest_streak,
        total_contributions=user.contribution_count,
        languages=languages,
        last_sync=sync_state.last_success_at if sync_state else None,
    )

    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, s-maxage=3600, stale-while-revalidate=86400",
        },
    )


@router.get("/{username}/cards/streak.svg")
def get_streak_card(username: str) -> Response:
    """
    Generate and return a contribution streak SVG card.

    Args:
        username: GitHub username

    Returns:
        SVG image response with streak statistics
    """
    with get_db() as session:
        user = UserRepository.get_by_username(session, username)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {username} not found")

        sync_state = SyncStateRepository.get(session, username)

    svg_content = generate_streak_card(
        username=user.username,
        current_streak=user.current_streak,
        longest_streak=user.longest_streak,
        total_contributions=user.contribution_count,
        last_sync=sync_state.last_success_at if sync_state else None,
    )

    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, s-maxage=3600, stale-while-revalidate=86400",
        },
    )


@router.get("/{username}/cards/languages.svg")
def get_languages_card(username: str) -> Response:
    """
    Generate and return a top languages SVG card.

    Args:
        username: GitHub username

    Returns:
        SVG image response with top 6 languages
    """
    with get_db() as session:
        user = UserRepository.get_by_username(session, username)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {username} not found")

        language_totals = LanguageRepository.get_all_for_user(session, username)
        sync_state = SyncStateRepository.get(session, username)

    # Extract top 6 languages with percentages
    if not language_totals:
        # Return empty card if no languages
        languages = []
    else:
        total_bytes = sum(lang.byte_count for lang in language_totals)
        languages = [
            (lang.language, (lang.byte_count / total_bytes) * 100) for lang in language_totals[:6]
        ]

    svg_content = generate_languages_card(
        username=user.username,
        languages=languages,
        last_sync=sync_state.last_success_at if sync_state else None,
    )

    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, s-maxage=3600, stale-while-revalidate=86400",
        },
    )
