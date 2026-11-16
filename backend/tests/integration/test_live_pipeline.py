from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from observatorio.consumer.processor import persist_message
from observatorio.models import (
    Base,
    EventCurrent,
    EventVersion,
    IngestionRun,
    PublishedPayload,
    SourceArchive,
)
from observatorio.producer import archive, live
from observatorio.producer.source import FeedResponse


@pytest_asyncio.fixture
async def live_database(monkeypatch, tmp_path):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(live, "session_factory", factory)

    original_archive_response = archive.archive_response

    async def archive_to_tmp(content, **kwargs):
        return await original_archive_response(content, directory=tmp_path, **kwargs)

    monkeypatch.setattr(live, "archive_response", archive_to_tmp)
    yield factory, tmp_path
    await engine.dispose()


@pytest.mark.asyncio
async def test_live_event_is_persisted_idempotently_with_latest_current_version() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    def message(updated: int) -> bytes:
        return json.dumps(
            {
                "id": "live-integration",
                "mode": "live",
                "source": "usgs-live",
                "ingestion_run_id": str(uuid4()),
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "type": "Feature",
                    "id": "live-integration",
                    "properties": {
                        "type": "earthquake",
                        "time": 1_760_000_000_000,
                        "updated": updated,
                        "mag": 5.2,
                    },
                    "geometry": {"type": "Point", "coordinates": [-3.7, 40.4, 12.0]},
                },
            }
        ).encode()

    older, newer = 1_760_000_001_000, 1_760_000_002_000
    assert await persist_message(factory, message(older), topic="quakes.live", partition=0, offset=0) == "persisted"
    assert await persist_message(factory, message(newer), topic="quakes.live", partition=0, offset=1) == "persisted"
    assert await persist_message(factory, message(older), topic="quakes.live", partition=0, offset=2) == "duplicate"
    async with factory() as session:
        versions = (await session.scalars(select(EventVersion).where(EventVersion.mode == "live"))).all()
        current = await session.get(EventCurrent, ("live", "live-integration"))
    await engine.dispose()

    assert len(versions) == 2
    assert all(version.original_payload["id"] == "live-integration" for version in versions)
    assert current is not None
    assert current.current_updated_at.replace(tzinfo=timezone.utc) == datetime.fromtimestamp(newer / 1000, tz=timezone.utc)


@pytest.mark.asyncio
async def test_live_archives_complete_response_before_ack_and_preserves_failed_poll_state(
    live_database,
    monkeypatch,
) -> None:
    factory, archive_dir = live_database
    feature = {
        "type": "Feature",
        "id": "live-source-event",
        "properties": {
            "type": "earthquake",
            "time": 1_760_000_000_000,
            "updated": 1_760_000_000_000,
            "mag": 4.7,
            "source_extension": {"preserved": True},
        },
        "geometry": {"type": "Point", "coordinates": [-3.7, 40.4, 8.0]},
        "bbox": [-3.8, 40.3, 8.0, -3.6, 40.5, 8.0],
        "foreign_member": ["kept"],
    }
    original_response = json.dumps(
        {"type": "FeatureCollection", "metadata": {"generated": 123}, "features": [feature]},
        separators=(",", ":"),
    ).encode()
    fetches = 0

    async def fetch_response(url, *, timeout):
        nonlocal fetches
        fetches += 1
        now = datetime.now(timezone.utc)
        return FeedResponse(
            url=url,
            status_code=200,
            content=original_response,
            payload=json.loads(original_response),
            requested_at=now,
            received_at=now,
            attempts=1,
        )

    class FakeProducer:
        async def send_and_wait(self, topic, *, value, key):
            envelope = json.loads(value)
            async with factory() as session:
                run = await session.get(IngestionRun, UUID(envelope["ingestion_run_id"]))
                archive_row = await session.scalar(select(SourceArchive))
            assert archive_row is not None
            assert Path(archive_row.storage_path).read_bytes() == original_response
            assert run is not None
            assert run.source_archive_sha256 == archive_row.sha256
            assert envelope["payload"] == feature
            assert envelope["payload"]["foreign_member"] == ["kept"]
            return SimpleNamespace(partition=0, offset=0)

        async def stop(self):
            return None

    async def create_fake_producer():
        return FakeProducer()

    monkeypatch.setattr(live, "fetch_recent_response", fetch_response)
    monkeypatch.setattr(live, "create_producer", create_fake_producer)

    result = await live.tick_once()
    assert len(result) == 1

    async with factory() as session:
        runs = (await session.scalars(select(IngestionRun))).all()
        archives = (await session.scalars(select(SourceArchive))).all()
        publications = (await session.scalars(select(PublishedPayload))).all()
    assert len(runs) == len(archives) == len(publications) == 1
    assert runs[0].outcome == "succeeded"
    assert runs[0].records_received == 1
    assert archives[0].storage_path.startswith(str(archive_dir))

    repeated = await live.tick_once()
    assert repeated == []
    async with factory() as session:
        runs = (await session.scalars(select(IngestionRun).order_by(IngestionRun.started_at))).all()
        archives = (await session.scalars(select(SourceArchive))).all()
        publications = (await session.scalars(select(PublishedPayload))).all()
    assert fetches == 2
    assert len(runs) == 2 and all(run.outcome == "succeeded" for run in runs)
    assert runs[0].source_archive_sha256 == runs[1].source_archive_sha256
    assert len(archives) == len(publications) == 1

    async def failed_fetch(url, *, timeout):
        raise ConnectionError("feed is unavailable")

    monkeypatch.setattr(live, "fetch_recent_response", failed_fetch)
    with pytest.raises(ConnectionError):
        await live.tick_once()
    async with factory() as session:
        runs = (await session.scalars(select(IngestionRun).order_by(IngestionRun.started_at))).all()
    assert [run.outcome for run in runs] == ["succeeded", "succeeded", "failed"]
