"""SVG card API endpoints."""

import logging

from fastapi import APIRouter, Response

from app.api.common import CACHE_NONE, CACHE_NOT_FOUND, CACHE_OK, is_valid_username
from app.cards import CARDS, generate_error_card
from app.exceptions import GithubApiError, GithubNotFoundError
from app.stats.service import get_user_stats

router = APIRouter(prefix="/v1/users", tags=["cards"])
logger = logging.getLogger(__name__)


def _svg(content: str, cache_control: str, status_code: int = 200) -> Response:
    return Response(
        content=content,
        status_code=status_code,
        media_type="image/svg+xml",
        headers={"Cache-Control": cache_control},
    )


@router.get("/{username}/cards/{card}.svg")
async def get_card(username: str, card: str) -> Response:
    """Render a card. Always answers with an SVG — errors are drawn as an
    error card, because a non-image response shows up as a broken image
    in a README with no hint of what went wrong.

    Bad input answers 200 (a stable, cacheable answer). A GitHub outage
    answers 503: a 200 would count as a successful revalidation and
    replace the good card in the CDN, while a 5xx makes the CDN keep
    serving its stale copy (stale-if-error)."""
    if card not in CARDS:
        return _svg(
            generate_error_card(username, "unknown card", f"use one of: {', '.join(CARDS)}"),
            CACHE_NOT_FOUND,
        )
    if not is_valid_username(username):
        return _svg(
            generate_error_card(username, "invalid username", "check the URL"),
            CACHE_NOT_FOUND,
        )

    try:
        stats = await get_user_stats(username)
    except GithubNotFoundError:
        return _svg(
            generate_error_card(username, "user not found", "check the username in the URL"),
            CACHE_NOT_FOUND,
        )
    except GithubApiError as e:
        logger.error(f"Card {card} for {username} failed: {e}")
        return _svg(
            generate_error_card(username, "GitHub unavailable", "temporary - will retry shortly"),
            CACHE_NONE,
            status_code=503,
        )

    return _svg(CARDS[card](stats), CACHE_OK)
