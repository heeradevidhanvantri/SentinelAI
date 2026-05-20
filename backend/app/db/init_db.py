"""Database URL normalization, schema initialization, and demo user seeding."""

from __future__ import annotations

from sqlalchemy import inspect, select, text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import get_settings
from app.core.auth import Role, hash_password
from app.core.logging import get_logger
from app.db.base import Base, engine, normalize_database_url
from app.models.user import User, Tenant

# Import all models so metadata is complete before create_all
import app.models.incident  # noqa: F401
import app.models.metric  # noqa: F401
import app.models.remediation  # noqa: F401

logger = get_logger(__name__)

DEMO_USER_EMAIL = "admin@sentinelai.io"
DEMO_USER_PASSWORD = "sentinel123"


def normalize_database_url(url: str) -> str:
    """Re-export for scripts; canonical implementation lives in app.db.base."""
    from app.db.base import normalize_database_url as _normalize
    return _normalize(url)


async def init_database(db_engine: AsyncEngine | None = None) -> None:
    """Create all ORM tables if they do not exist."""
    db_engine = db_engine or engine
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_schema_initialized")


async def users_table_exists(db_engine: AsyncEngine | None = None) -> bool:
    db_engine = db_engine or engine

    def _check(connection):
        return inspect(connection).has_table("users")

    async with db_engine.connect() as conn:
        return await conn.run_sync(_check)


async def check_database_connectivity(db_engine: AsyncEngine | None = None) -> bool:
    db_engine = db_engine or engine
    try:
        async with db_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def ensure_demo_user(db_engine: AsyncEngine | None = None) -> User | None:
    """Create production demo admin if missing."""
    from app.db.base import async_session_factory

    settings = get_settings()
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.email == DEMO_USER_EMAIL))
        existing = result.scalar_one_or_none()
        if existing:
            logger.info("demo_user_exists", email=DEMO_USER_EMAIL)
            return existing

        tenant_result = await session.execute(
            select(Tenant).where(Tenant.id == settings.default_tenant_id)
        )
        if tenant_result.scalar_one_or_none() is None:
            session.add(
                Tenant(
                    id=settings.default_tenant_id,
                    name="Default Tenant",
                    slug=settings.default_tenant_id,
                    is_active=True,
                )
            )

        user = User(
            email=DEMO_USER_EMAIL,
            tenant_id=settings.default_tenant_id,
            hashed_password=hash_password(DEMO_USER_PASSWORD),
            full_name="SentinelAI Admin",
            role=Role.ADMIN,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("demo_user_created", email=DEMO_USER_EMAIL, user_id=user.id)
        return user
