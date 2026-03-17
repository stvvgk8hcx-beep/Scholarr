"""Database engine setup and session management."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import async_sessionmaker

Base = declarative_base()


def create_engine(database_url: str) -> AsyncEngine:
    """Create AsyncEngine with proper configuration.

    Supports SQLite (dev), MySQL (production), and PostgreSQL.
    MySQL uses aiomysql driver: mysql+aiomysql://user:pass@host/db
    """
    if "sqlite" in database_url:
        return create_async_engine(
            database_url,
            echo=False,
            connect_args={"check_same_thread": False},
        )
    elif "mysql" in database_url:
        return create_async_engine(
            database_url,
            echo=False,
            pool_size=20,
            max_overflow=10,
            pool_recycle=3600,
            pool_pre_ping=True,
        )
    elif "postgresql" in database_url:
        return create_async_engine(
            database_url,
            echo=False,
            pool_size=20,
            max_overflow=0,
        )
    else:
        raise ValueError(f"Unsupported database URL: {database_url}")


async_session_factory: async_sessionmaker | None = None


def init_db(database_url: str) -> None:
    """Initialize database engine and session factory."""
    global async_session_factory
    engine = create_engine(database_url)
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI endpoints to get async database session."""
    if async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
