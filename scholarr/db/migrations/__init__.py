"""Database migration helpers."""

import logging

logger = logging.getLogger(__name__)


async def run_migrations() -> None:
    """Run database migrations.

    For production, this should run Alembic migrations.
    For SQLite dev environments, it falls back to create_all.
    """
    from scholarr.core.config import settings

    if "sqlite" in settings.database_url:
        # SQLite dev mode — create all tables directly
        from scholarr.db.session import async_engine
        from scholarr.db.base import Base
        import scholarr.db.models  # noqa: F401 — ensures models are registered

        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("SQLite tables created via create_all")
        return

    # Production: delegate to Alembic
    try:
        import asyncio
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config("alembic.ini")

        def _run(cfg: Config) -> None:
            command.upgrade(cfg, "head")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _run, alembic_cfg)
        logger.info("Alembic migrations applied")
    except Exception as exc:
        logger.warning(f"Alembic migration failed, skipping: {exc}")
