"""Synchronization API endpoints."""

import asyncio
import logging
import secrets
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.db.connection import get_db
from app.db.repositories import SyncStateRepository
from app.sync.service import sync_user_background

router = APIRouter(prefix="/v1/sync", tags=["sync"])
logger = logging.getLogger(__name__)


class SyncScheduledResponse(BaseModel):
    """Response confirming a sync has been scheduled."""

    username: str
    status: str
    message: str


def verify_sync_secret(authorization: Annotated[str | None, Header()] = None) -> None:
    """Verify sync secret from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    parts = authorization.split()
    if (
        len(parts) != 2
        or parts[0].lower() != "bearer"
        or not secrets.compare_digest(parts[1], settings.sync_secret)
    ):
        raise HTTPException(status_code=401, detail="Invalid authorization format or secret")


def _is_locked_sync(username: str) -> bool:
    """Cheap single-row read of whether a sync is currently running for
    this user — not the full sync itself, so it's safe to do inline
    before scheduling the background task. This is a fast-fail
    optimization only: the authoritative lock check still happens
    atomically inside sync_user's own acquire_lock. A near-simultaneous
    second request can still pass this check before the first
    request's background task actually acquires the lock — in that
    rare race, sync_user_background silently no-ops on the loser side
    (it catches SyncAlreadyRunningError), which is harmless since the
    winner's sync still completes the work.
    """
    with get_db() as session:
        sync_state = SyncStateRepository.get(session, username)

    if sync_state is None or sync_state.locked_until is None:
        return False
    return sync_state.locked_until > datetime.now(UTC)


@router.post("/{username}", response_model=SyncScheduledResponse, status_code=202)
async def sync_user(
    username: str,
    background_tasks: BackgroundTasks,
    _: Annotated[None, Depends(verify_sync_secret)],
) -> SyncScheduledResponse:
    """
    Schedule synchronization for a GitHub user.

    Returns 202 as soon as the sync is scheduled rather than waiting
    for it to complete. Sync duration depends on repo count and GitHub
    API latency and can legitimately exceed typical HTTP client
    timeouts — waiting for full completion inside the request was the
    actual cause of prior "hangs" that were really just successful
    syncs taking longer than the caller's timeout allowed.

    The sync itself runs via FastAPI BackgroundTasks, not a detached
    thread — it's part of the ASGI request lifecycle, so the platform
    won't freeze the process before it finishes (see
    sync_user_background's docstring in app/sync/service.py).

    To confirm a sync actually completed, poll
    GET /v1/users/{username}/stats and check meta.sync_status and
    meta.last_sync — this endpoint only confirms scheduling, not
    completion.

    Raises:
        409: A sync is already running for this user
    """
    if await asyncio.to_thread(_is_locked_sync, username):
        raise HTTPException(
            status_code=409,
            detail=f"Synchronization already in progress for {username}",
        )

    background_tasks.add_task(sync_user_background, username)

    return SyncScheduledResponse(
        username=username,
        status="scheduled",
        message=f"Synchronization scheduled for {username} — check "
        f"/v1/users/{username}/stats for completion",
    )
