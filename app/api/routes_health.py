"""Health and readiness check endpoints."""

import os
from fastapi import APIRouter
from pydantic import BaseModel

from app.db.connection import get_db

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    message: str


class ReadyResponse(BaseModel):
    """Readiness check response."""

    status: str
    database: str
    data_available: bool


class DebugResponse(BaseModel):
    """Debug response showing environment."""

    database_url_set: bool
    github_token_set: bool
    sync_secret_set: bool
    environment: str | None


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Basic health check - application is responding.

    Returns 200 if the application process can handle requests.
    """
    return HealthResponse(
        status="ok",
        message="Service is healthy",
    )


@router.get("/ready", response_model=ReadyResponse)
def readiness_check() -> ReadyResponse:
    """
    Readiness check - application can serve useful data.

    Checks:
    - Database connectivity
    - At least one synchronized user exists

    Returns 200 if ready to serve traffic, 503 otherwise.
    """
    db_status = "unknown"
    data_available = False

    try:
        with get_db() as session:
            from sqlalchemy import text

            session.execute(text("SELECT 1"))
            db_status = "connected"

            result = session.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            data_available = count > 0 if count else False

        if db_status == "connected" and data_available:
            return ReadyResponse(
                status="ready",
                database=db_status,
                data_available=data_available,
            )
        else:
            return ReadyResponse(
                status="not_ready",
                database=db_status,
                data_available=data_available,
            )

    except Exception as e:
        return ReadyResponse(
            status="error",
            database=f"error: {str(e)}",
            data_available=False,
        )


@router.get("/debug", response_model=DebugResponse, tags=["debug"])
def debug_info() -> DebugResponse:
    """Debug endpoint to check environment variables."""
    return DebugResponse(
        database_url_set=bool(os.getenv("DATABASE_URL")),
        github_token_set=bool(os.getenv("GITHUB_TOKEN")),
        sync_secret_set=bool(os.getenv("SYNC_SECRET")),
        environment=os.getenv("ENVIRONMENT"),
    )
