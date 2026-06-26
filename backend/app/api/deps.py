"""API dependencies — database session and service injection.

In FAKE_MODE: skips DB entirely, no PostgreSQL required.
In production: connects to real PostgreSQL via SQLAlchemy async.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings


def _real_db_generator():
    """Lazy-load real DB generator (only imported when NOT in fake mode)."""
    from app.models.database import async_session

    async def _inner():
        async with async_session() as session:
            yield session

    return _inner


async def get_db() -> AsyncGenerator[AsyncSession | None, None]:
    """Yield an async database session.

    In FAKE_MODE: yields None (no DB needed).
    In production: yields a real AsyncSession.
    """
    if settings.fake_mode:
        yield None
        return

    gen = _real_db_generator()
    async for session in gen():
        yield session


def get_analysis_service():
    """Return AnalysisService (production mode only, requires DB)."""
    from app.services.analysis_service import AnalysisService
    return AnalysisService()
