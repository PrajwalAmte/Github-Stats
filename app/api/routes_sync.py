"""Synchronization API endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.exceptions import GithubApiError, GithubNotFoundError, SyncAlreadyRunningError
from app.sync.service import sync_service

router = APIRouter(prefix="/v1/sync", tags=["sync"])
logger = logging.getLogger(__name__)


class SyncResponse(BaseModel):
    """Sync operation response."""

    username: str
    status: str
    message: str
    repositories_synced: int | None = None
    contribution_days: int | None = None


def verify_sync_secret(authorization: Annotated[str | None, Header()] = None) -> None:
    """Verify sync secret from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or parts[1] != settings.sync_secret:
        raise HTTPException(status_code=401, detail="Invalid authorization format or secret")


@router.post("/{username}", response_model=SyncResponse)
async def sync_user(
    username: str,
    _: Annotated[None, Depends(verify_sync_secret)],
) -> SyncResponse:
    """
    Trigger synchronization for a GitHub user.

    Requires authentication via Bearer token in Authorization header.
    The sync is idempotent and will skip if already running.

    Args:
        username: GitHub username to synchronize

    Returns:
        SyncResponse with operation details

    Raises:
        409: Sync already running for this user
        404: GitHub user not found
        500: GitHub API error or internal error
    """
    try:
        result = await sync_service.sync_user(username)

        return SyncResponse(
            username=username,
            status="success",
            message="Synchronization completed successfully",
            repositories_synced=result.get("repositories_synced"),
            contribution_days=result.get("contribution_days"),
        )

    except SyncAlreadyRunningError:
        raise HTTPException(
            status_code=409,
            detail=f"Synchronization already in progress for {username}",
        )

    except GithubNotFoundError as e:
        logger.warning(f"User not found: {username}")
        raise HTTPException(status_code=404, detail=str(e))

    except GithubApiError as e:
        logger.error(f"GitHub API error for {username}: {e}")
        raise HTTPException(status_code=500, detail="GitHub API error occurred")

    except Exception as e:
        logger.error(f"Unexpected error syncing {username}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
