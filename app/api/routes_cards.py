"""SVG card API endpoints."""

import logging

from fastapi import APIRouter, BackgroundTasks, Response

from app.api.common import ensure_user_syncing
from app.cards.languages import generate_languages_card
from app.cards.overview import generate_overview_card
from app.cards.profile import generate_profile_card
from app.cards.streak import generate_streak_card
from app.db.connection import get_db
from app.db.repositories import LanguageRepository, SyncStateRepository, UserRepository

router = APIRouter(prefix="/v1/users", tags=["cards"])
logger = logging.getLogger(__name__)


def generate_loading_card(username: str) -> str:
    """Generate a placeholder card shown while profile is syncing."""
    return f"""<svg width="1100" height="260" viewBox="0 0 1100 260" xmlns="http://www.w3.org/2000/svg">
  <rect width="1100" height="260" rx="10" fill="#0b0e14"/>
  <rect x="0.5" y="0.5" width="1099" height="259" rx="10" fill="none" stroke="#232a3d"/>

  <rect x="0" y="0" width="1100" height="40" rx="10" fill="#161c2c"/>
  <circle cx="18" cy="20" r="4.5" fill="#e5534b" opacity="0.75"/>
  <circle cx="34" cy="20" r="4.5" fill="#e2b93d" opacity="0.75"/>
  <circle cx="50" cy="20" r="4.5" fill="#57ab5a" opacity="0.75"/>
  <text x="550" y="25" text-anchor="middle" font-family="monospace" font-size="11" fill="#5c6370">Syncing your profile...</text>

  <text x="550" y="130" text-anchor="middle" font-family="monospace" font-size="16" fill="#d5dae3">
    Loading stats for {username}
  </text>
  <text x="550" y="160" text-anchor="middle" font-family="monospace" font-size="12" fill="#5c6370">
    This usually takes 10-30 seconds. Refresh in a moment.
  </text>
</svg>"""


@router.get("/{username}/cards/profile.svg")
def get_profile_card(username: str, background_tasks: BackgroundTasks) -> Response:
    """
    Generate and return a profile statistics SVG card.

    Args:
        username: GitHub username

    Returns:
        SVG image response with profile statistics
    """
    # Auto-trigger sync if user not found
    if not ensure_user_syncing(username, background_tasks):
        return Response(
            content=generate_loading_card(username),
            media_type="image/svg+xml",
            headers={"Cache-Control": "no-cache, no-store"},
        )

    with get_db() as session:
        user = UserRepository.get_by_username(session, username)
        if not user:
            return Response(
                content=generate_loading_card(username),
                media_type="image/svg+xml",
                headers={"Cache-Control": "no-cache, no-store"},
            )

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
def get_overview_card(username: str, background_tasks: BackgroundTasks) -> Response:
    """Generate and return a consolidated wide SVG card."""
    # Auto-trigger sync if user not found
    if not ensure_user_syncing(username, background_tasks):
        return Response(
            content=generate_loading_card(username),
            media_type="image/svg+xml",
            headers={"Cache-Control": "no-cache, no-store"},
        )

    with get_db() as session:
        user = UserRepository.get_by_username(session, username)
        if not user:
            return Response(
                content=generate_loading_card(username),
                media_type="image/svg+xml",
                headers={"Cache-Control": "no-cache, no-store"},
            )

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
def get_streak_card(username: str, background_tasks: BackgroundTasks) -> Response:
    """
    Generate and return a contribution streak SVG card.

    Args:
        username: GitHub username

    Returns:
        SVG image response with streak statistics
    """
    # Auto-trigger sync if user not found
    if not ensure_user_syncing(username, background_tasks):
        return Response(
            content=generate_loading_card(username),
            media_type="image/svg+xml",
            headers={"Cache-Control": "no-cache, no-store"},
        )

    with get_db() as session:
        user = UserRepository.get_by_username(session, username)
        if not user:
            return Response(
                content=generate_loading_card(username),
                media_type="image/svg+xml",
                headers={"Cache-Control": "no-cache, no-store"},
            )

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
def get_languages_card(username: str, background_tasks: BackgroundTasks) -> Response:
    """
    Generate and return a top languages SVG card.

    Args:
        username: GitHub username

    Returns:
        SVG image response with top 6 languages
    """
    # Auto-trigger sync if user not found
    if not ensure_user_syncing(username, background_tasks):
        return Response(
            content=generate_loading_card(username),
            media_type="image/svg+xml",
            headers={"Cache-Control": "no-cache, no-store"},
        )

    with get_db() as session:
        user = UserRepository.get_by_username(session, username)
        if not user:
            return Response(
                content=generate_loading_card(username),
                media_type="image/svg+xml",
                headers={"Cache-Control": "no-cache, no-store"},
            )

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
