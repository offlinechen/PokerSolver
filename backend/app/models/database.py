"""SQLAlchemy async engine and session configuration.

Engine is lazy-loaded to avoid crashing on import when running in FAKE_MODE
or when the database is not yet available.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

_engine = None
_async_session = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.app_env == "development",
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def _get_async_session():
    global _async_session
    if _async_session is None:
        _async_session = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session


# Legacy aliases for backward compatibility (access via property-like functions)
# Direct access to engine/async_session is deprecated; use async_session() via get_db
def __getattr__(name):
    if name == "engine":
        return _get_engine()
    if name == "async_session":
        return _get_async_session()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """Dependency: yield an async database session."""
    session_factory = _get_async_session()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
