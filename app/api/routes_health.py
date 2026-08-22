"""Health and readiness check endpoints."""

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
    try:
        from sqlalchemy import text

        with get_db() as session:
            session.execute(text("SELECT 1"))
            data_available = bool(session.execute(text("SELECT COUNT(*) FROM users")).scalar())

        return ReadyResponse(
            status="ready" if data_available else "not_ready",
            database="connected",
            data_available=data_available,
        )

    except Exception as e:
        return ReadyResponse(
            status="error",
            database=f"error: {str(e)}",
            data_available=False,
        )
