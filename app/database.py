from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from typing import AsyncGenerator

from app.config import settings

_engine_kwargs = {"echo": settings.sql_echo}

if settings.database_url.startswith("postgresql"):
    _engine_kwargs.update(
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )

engine = create_async_engine(settings.database_url, **_engine_kwargs)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
