"""
FastAPI dependency injection functions.
"""

from typing import Generator

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from sqlalchemy.orm import Session, sessionmaker

from common.config import Settings

security = HTTPBearer()


def get_settings(request: Request) -> Settings:
    """
    Get application settings from request state.

    Args:
        request: FastAPI request object

    Returns:
        Settings: Application settings instance
    """
    return request.app.state.settings


def get_session_factory(request: Request) -> sessionmaker[Session]:
    """
    Get database session factory from request state.

    Args:
        request: FastAPI request object

    Returns:
        sessionmaker: Session factory
    """
    return request.app.state.session_factory


def get_db(
    session_factory: sessionmaker[Session] = Depends(
        get_session_factory
    )
) -> Generator[Session, None, None]:
    """
    Provide database session for request handlers.

    Args:
        session_factory: SQLAlchemy session factory

    Yields:
        Session: Database session
    """
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_redis(request: Request) -> Redis:
    """
    Get Redis client from request state.

    Args:
        request: FastAPI request object

    Returns:
        Redis: Redis client instance
    """
    return request.app.state.redis_client


def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    settings: Settings = Depends(get_settings)
) -> str:
    """
    Verify static bearer token authentication.

    Args:
        credentials: HTTP authorization credentials
        settings: Application settings

    Returns:
        str: Verified token

    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials

    if token != settings.static_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

    return token
