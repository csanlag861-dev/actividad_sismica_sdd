from __future__ import annotations

import hashlib

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from observatorio.models import Base, IngestionRun, SourceArchive
from observatorio.producer.archive import archive_response, cleanup_unreferenced_archives


@pytest_asyncio.fixture
async def archive_sessions():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_response_archive_is_atomic_and_deduplicated(tmp_path, archive_sessions) -> None:
    content = b'{"type":"FeatureCollection","features":[]}'

    first = await archive_response(
        content,
        source="usgs-live",
        directory=tmp_path,
        session_factory_override=archive_sessions,
    )
    second = await archive_response(
        content,
        source="usgs-live",
        directory=tmp_path,
        session_factory_override=archive_sessions,
    )

    async with archive_sessions() as session:
        rows = (await session.scalars(select(SourceArchive))).all()
    assert first.sha256 == second.sha256 == hashlib.sha256(content).hexdigest()
    assert first.path == second.path
    assert first.path.read_bytes() == content
    assert len(rows) == 1
    assert rows[0].size_bytes == len(content)


@pytest.mark.asyncio
async def test_empty_completed_archive_cleanup_is_auditable(tmp_path, archive_sessions) -> None:
    from datetime import datetime, timezone
    from uuid import uuid4

    run_id = uuid4()
    async with archive_sessions() as session:
        async with session.begin():
            session.add(
                IngestionRun(
                    run_id=run_id,
                    mode="live",
                    source="usgs-live",
                    started_at=datetime.now(timezone.utc),
                    outcome="succeeded",
                    records_received=0,
                )
            )
    archived = await archive_response(
        b'{"type":"FeatureCollection","features":[]}',
        source="usgs-live",
        directory=tmp_path,
        ingestion_run_id=run_id,
        session_factory_override=archive_sessions,
    )

    removed = await cleanup_unreferenced_archives(
        session_factory_override=archive_sessions,
    )
    async with archive_sessions() as session:
        row = await session.get(SourceArchive, archived.sha256)
    assert removed == [archived.sha256]
    assert not archived.path.exists()
    assert row is not None and row.deleted_at is not None


@pytest.mark.asyncio
async def test_archive_with_received_records_is_retained(tmp_path, archive_sessions) -> None:
    from datetime import datetime, timezone
    from uuid import uuid4

    run_id = uuid4()
    async with archive_sessions() as session:
        async with session.begin():
            session.add(
                IngestionRun(
                    run_id=run_id,
                    mode="live",
                    source="usgs-live",
                    started_at=datetime.now(timezone.utc),
                    outcome="succeeded",
                    records_received=1,
                )
            )
    archived = await archive_response(
        b'{"type":"FeatureCollection","features":[{}]}',
        source="usgs-live",
        directory=tmp_path,
        ingestion_run_id=run_id,
        session_factory_override=archive_sessions,
    )

    removed = await cleanup_unreferenced_archives(
        session_factory_override=archive_sessions,
    )
    assert removed == []
    assert archived.path.is_file()
