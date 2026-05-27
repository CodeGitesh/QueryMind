"""
SQLAlchemy 2.0 async database session factory.
"""
from __future__ import annotations

from typing import AsyncIterator

import structlog
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

log = structlog.get_logger(__name__)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


# ── Engine ────────────────────────────────────────────────────────────────────
def _build_engine() -> AsyncEngine:
    db_url = settings.effective_database_url
    kwargs: dict = {
        "echo": settings.DATABASE_ECHO,
        "future": True,
    }
    if not settings.USE_SQLITE:
        kwargs.update(
            {
                "pool_size": settings.DATABASE_POOL_SIZE,
                "max_overflow": settings.DATABASE_MAX_OVERFLOW,
                "pool_pre_ping": True,
                "pool_recycle": 300,
            }
        )
    return create_async_engine(db_url, **kwargs)


engine: AsyncEngine = _build_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def create_db_and_tables() -> None:
    """Create all tables defined in ORM models (used on startup)."""
    from app.db import models  # noqa: F401 — ensure models are registered

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("All ORM tables created / verified")


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency — yields an async SQLAlchemy session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
