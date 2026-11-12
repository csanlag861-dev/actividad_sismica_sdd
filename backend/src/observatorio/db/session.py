from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from observatorio.config import settings

engine = create_async_engine(
    settings.sqlalchemy_database_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
)
session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


async def create_db_session() -> AsyncSession:
    return session_factory()
