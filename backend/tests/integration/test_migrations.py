from __future__ import annotations

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

from observatorio.db.catalog import ensure_country_catalog
from observatorio.models import Base, Country


@pytest.mark.asyncio
async def test_model_metadata_creates_required_tables() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with engine.connect() as conn:
        rows = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = set(rows.scalars())
    assert {
        "country",
        "calendar_date",
        "ingestion_run",
        "event_version",
        "event_current",
        "event_version_source",
        "published_version",
        "published_payload",
        "quarantine",
        "source_archive",
        "ingestion_interval",
    }.issubset(tables)
    await engine.dispose()


def test_event_time_index_matches_recent_event_queries() -> None:
    from observatorio.models import EventVersion

    indexes = {index.name: index for index in EventVersion.__table__.indexes}
    assert "ix_event_version_mode_event_time" in indexes


@pytest.mark.asyncio
async def test_seed_country_catalog_is_idempotent() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        first = await ensure_country_catalog(session)
    async with sessions() as session:
        second = await ensure_country_catalog(session)
        count = await session.scalar(select(func.count()).select_from(Country))
    assert len(first) == len(second) == 177
    assert count == 177
    await engine.dispose()


def test_settings_default_to_internal_service_names() -> None:
    from observatorio.config import Settings

    settings = Settings(postgres_host="postgres", postgres_password="runtime-value")
    assert "postgres:5432" in settings.postgres_dsn
    assert "kafka:9092" in settings.kafka_bootstrap_servers
