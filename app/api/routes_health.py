"""Health check endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    github_tokens: int


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """The process is up and has at least one GitHub token to work with."""
    tokens = len(settings.github_tokens)
    return HealthResponse(status="ok" if tokens else "misconfigured", github_tokens=tokens)
