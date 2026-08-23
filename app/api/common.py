"""Common utilities for API endpoints."""

from datetime import UTC, datetime

from fastapi import BackgroundTasks

from app.db.connection import get_db
from app.db.repositories import UserRepository
from app.sync.service import sync_user_background


def ensure_user_syncing(username: str, background_tasks: BackgroundTasks) -> bool:
    """
    Check if user has data; if not, schedule a background sync.

    Uses FastAPI's BackgroundTasks (not a detached thread) so the sync
    actually gets a chance to run before the platform can freeze the
    process post-response — see sync_user_background's docstring.

    Returns True if data exists, False if sync was scheduled.
    """
    with get_db() as session:
        user = UserRepository.get_by_username(session, username)
        if user:
            return True

    background_tasks.add_task(sync_user_background, username)
    return False


def get_loading_placeholder(username: str) -> dict:
    """Return a placeholder response while syncing."""
    return {
        "status": "syncing",
        "message": f"Fetching GitHub stats for {username}... please refresh in 30 seconds",
        "generated_at": datetime.now(UTC).isoformat(),
        "retry_after": 30,
    }
