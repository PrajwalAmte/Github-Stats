"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import routes_cards, routes_health, routes_stats, routes_sync
from app.config import settings
from app.db.connection import close_pool

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting GitHub Stats Service")
    logger.info(f"Environment: {settings.environment}")
    yield
    logger.info("Shutting down GitHub Stats Service")
    close_pool()


# Create FastAPI application
app = FastAPI(
    title="GitHub Stats Service",
    description="Production-quality GitHub statistics service for README profiles",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected exceptions gracefully."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Include routers
app.include_router(routes_health.router)
app.include_router(routes_sync.router)
app.include_router(routes_stats.router)
app.include_router(routes_cards.router)


@app.get("/")
def root():
    """Root endpoint with service information."""
    return {
        "service": "GitHub Stats Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "sync": "/v1/sync/{username}",
            "stats": "/v1/users/{username}/stats",
            "history": "/v1/users/{username}/history",
            "languages": "/v1/users/{username}/languages",
            "profile_card": "/v1/users/{username}/cards/profile.svg",
            "streak_card": "/v1/users/{username}/cards/streak.svg",
        },
    }


# Add cache control headers to all GET endpoints
@app.middleware("http")
async def add_cache_headers(request, call_next):
    """Add cache control headers to GET responses."""
    response = await call_next(request)

    # Only add cache headers to successful GET requests for user data
    if (
        request.method == "GET"
        and response.status_code == 200
        and request.url.path.startswith("/v1/users/")
    ):
        response.headers["Cache-Control"] = "public, s-maxage=3600, stale-while-revalidate=86400"

    return response
