"""Database connection and session management.

This module provides async SQLAlchemy session management and database initialization
for the YouTube dual-subtitles system.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ytb_dual_subtitles.core.settings import Settings, get_settings
from ytb_dual_subtitles.models import Base

logger = logging.getLogger(__name__)

# Global variables for database engine and session factory
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def create_engine(settings: Settings) -> AsyncEngine:
    """Create and configure the async database engine.

    Args:
        settings: Application settings containing database configuration.

    Returns:
        Configured async SQLAlchemy engine.
    """
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,  # Log SQL queries in debug mode
        future=True,
        # SQLite-specific options
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    )
    logger.info(f"Created database engine for {settings.database_url}")
    return engine


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create async session factory.

    Args:
        engine: Async SQLAlchemy engine.

    Returns:
        Async session factory.
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def init_database(settings: Settings | None = None) -> None:
    """Initialize database engine and create tables.

    Args:
        settings: Application settings. If None, uses global settings.
    """
    global _engine, _async_session_factory

    if settings is None:
        settings = get_settings()

    # Create engine and session factory
    _engine = create_engine(settings)
    _async_session_factory = create_session_factory(_engine)

    # Create all tables
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized successfully")


async def close_database() -> None:
    """Close database connections and clean up resources."""
    global _engine

    if _engine:
        await _engine.dispose()
        logger.info("Database connections closed")


def get_engine() -> AsyncEngine:
    """Get the global database engine.

    Returns:
        Async SQLAlchemy engine.

    Raises:
        RuntimeError: If database is not initialized.
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get the global session factory.

    Returns:
        Async session factory.

    Raises:
        RuntimeError: If database is not initialized.
    """
    if _async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _async_session_factory


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session.

    This is the main function to use for database operations.
    It provides a context manager that automatically handles session cleanup.

    Yields:
        Async SQLAlchemy session.

    Example:
        ```python
        async with get_db_session() as session:
            video = await session.get(Video, video_id)
            # ... perform database operations
        # Session is automatically closed here
        ```
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# FastAPI dependency function
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions.

    This function is used as a FastAPI dependency to inject database sessions
    into route handlers.

    Yields:
        Async SQLAlchemy session.

    Example:
        ```python
        @app.get("/videos/")
        async def get_videos(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Video))
            return result.scalars().all()
        ```
    """
    async with get_db_session() as session:
        yield session