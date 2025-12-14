"""
FastAPI application entrypoint for MOE API.

This module initializes the FastAPI app with all necessary
configurations, middleware, and route handlers.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.config import get_settings
from common.db import create_engine_from_url, create_session_factory
from common.logging_conf import setup_fastapi_logging

from .v1.router import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events for the application.
    """
    # Startup
    logger.info("Starting MOE API...")
    settings = get_settings()

    # Initialize logging with Sentry
    setup_fastapi_logging(
        sentry_dsn=settings.sentry_dsn,
        sentry_environment=settings.sentry_environment,
        sentry_traces_sample_rate=settings.sentry_traces_sample_rate,
        sentry_profiles_sample_rate=settings.sentry_profiles_sample_rate,
        log_level="DEBUG" if settings.debug else "INFO"
    )

    # Initialize database
    engine = create_engine_from_url(
        settings.db_url,
        echo=settings.debug
    )
    session_factory = create_session_factory(engine)

    # Initialize Redis
    redis_client = redis.from_url(
        settings.redis_url,
        decode_responses=True
    )

    # Store in app state
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.redis_client = redis_client

    logger.info("MOE API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down MOE API...")
    engine.dispose()
    redis_client.close()
    logger.info("MOE API shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title="MOE API",
        description="Math Olympiad Exercises API",
        version="0.1.0",
        lifespan=lifespan
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router)

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
