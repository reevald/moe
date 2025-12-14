"""
Database session and engine factory functions.

CRITICAL: This module does NOT create engine at import time.
Services must call create_engine_from_url() explicitly with
their configuration.
"""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def create_engine_from_url(
    database_url: str,
    pool_pre_ping: bool = True,
    pool_size: int = 5,
    max_overflow: int = 10,
    echo: bool = False
) -> Engine:
    """
    Create SQLAlchemy engine from database URL.

    Args:
        database_url: PostgreSQL connection URL
        pool_pre_ping: Enable connection health checks
        pool_size: Number of connections to maintain
        max_overflow: Maximum overflow connections
        echo: Enable SQL query logging

    Returns:
        Engine: Configured SQLAlchemy engine
    """
    return create_engine(
        database_url,
        pool_pre_ping=pool_pre_ping,
        pool_size=pool_size,
        max_overflow=max_overflow,
        echo=echo
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """
    Create session factory from engine.

    Args:
        engine: SQLAlchemy engine instance

    Returns:
        sessionmaker: Session factory for creating database sessions
    """
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )


def get_db_session(
    session_factory: sessionmaker[Session]
) -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session.

    Args:
        session_factory: SQLAlchemy session factory

    Yields:
        Session: Database session

    Note:
        This generator ensures proper session cleanup via try/finally.
    """
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
