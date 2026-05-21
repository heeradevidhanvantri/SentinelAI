"""SQLAlchemy base and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings
from app.db.url import normalize_database_url, normalize_database_url_with_connect_args

# Re-export for scripts and backward compatibility
__all__ = [
    "Base",
    "engine",
    "async_session_factory",
    "get_db",
    "get_engine",
    "normalize_database_url",
]


class Base(DeclarativeBase):
    pass


def get_engine():
    settings = get_settings()
    database_url, connect_args = normalize_database_url_with_connect_args(settings.database_url)
    engine_kwargs = {
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
        "echo": settings.app_env == "development",
    }
    if connect_args:
        engine_kwargs["connect_args"] = connect_args
    return create_async_engine(database_url, **engine_kwargs)


engine = get_engine()
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
