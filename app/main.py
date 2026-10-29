"""Main FastAPI application."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import routes_cards, routes_health, routes_stats
from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# Create FastAPI application
app = FastAPI(
    title="GitHub Stats Service",
    description="GitHub statistics cards for README profiles",
    version="2.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
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
        headers={"Cache-Control": "no-store"},
    )


# Include routers
app.include_router(routes_health.router)
app.include_router(routes_stats.router)
app.include_router(routes_cards.router)


@app.get("/")
def root():
    """Root endpoint with service information."""
    return {
        "service": "GitHub Stats Service",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "stats": "/v1/users/{username}/stats",
            "languages": "/v1/users/{username}/languages",
            "overview_card": "/v1/users/{username}/cards/overview.svg",
            "profile_card": "/v1/users/{username}/cards/profile.svg",
            "streak_card": "/v1/users/{username}/cards/streak.svg",
            "languages_card": "/v1/users/{username}/cards/languages.svg",
        },
    }
