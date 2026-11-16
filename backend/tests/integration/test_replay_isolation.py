from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from observatorio.consumer.processor import persist_message
from observatorio.models import (
    Base,
    EventCurrent,
    EventVersion,
    IngestionInterval,
    IngestionRun,
    SourceArchive,
)
from observatorio.producer import archive, replay


@pytest_asyncio.fixture
async def replay_database(monkeypatch, tmp_path):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(replay, "session_factory", factory)

    original_archive_response = archive.archive_response

    async def archive_to_tmp(content, **kwargs):
        return await original_archive_response(content, directory=tmp_path, **kwargs)

    monkeypatch.setattr(replay, "archive_response", archive_to_tmp)
    yield factory, tmp_path
    await engine.dispose()


@pytest.mark.asyncio
async def test_replay_events_are_isolated_from_live_rows() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    def message(mode: str) -> bytes:
        return json.dumps(
            {
                "id": "shared-event-id",
                "mode": mode,
                "source": f"usgs-{mode}",
                "ingestion_run_id": str(uuid4()),
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "type": "Feature",
                    "id": "shared-event-id",
                    "properties": {
                        "type": "earthquake",
                        "time": 1_760_000_000_000,
                        "updated": 1_760_000_000_000,
                    },
                    "geometry": {"type": "Point", "coordinates": [-3.7, 40.4, 10.0]},
                },
            }
        ).encode()

    await persist_message(factory, message("live"), topic="quakes.live", partition=0, offset=0)
    await persist_message(factory, message("replay"), topic="quakes.replay", partition=0, offset=0)
    async with factory() as session:
        versions = (await session.scalars(select(EventVersion))).all()
        live_before = await session.get(EventCurrent, ("live", "shared-event-id"))
        replay_current = await session.get(EventCurrent, ("replay", "shared-event-id"))
    await engine.dispose()

    assert {(item.mode, item.event_id) for item in versions} == {
        ("live", "shared-event-id"),
        ("replay", "shared-event-id"),
    }
    assert live_before is not None
    assert replay_current is not None


@pytest.mark.asyncio
async def test_replay_resumes_from_archived_interval_and_skips_completed_load(
    replay_database,
    monkeypatch,
) -> None:
    factory, archive_dir = replay_database
    requests: list[dict] = []
    feature = {
        "type": "Feature",
        "id": "replay-event",
        "properties": {
            "type": "earthquake",
            "time": 1_760_000_000_000,
            "updated": 1_760_000_000_000,
            "mag": 4.5,
        },
        "geometry": {"type": "Point", "coordinates": [-3.7, 40.4, 10.0]},
    }

    class FakeResponse:
        status_code = 200
        url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
        content = json.dumps(
            {"type": "FeatureCollection", "features": [feature]}
        ).encode()

        def raise_for_status(self):
            return None

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, *, params, timeout=None):
            requests.append(params)
            return FakeResponse()

    class FakeProducer:
        def __init__(self, fail_first: bool):
            self.fail_first = fail_first
            self.calls = 0
            self.stopped = 0

        async def send_and_wait(self, topic, *, value, key):
            self.calls += 1
            if self.fail_first:
                self.fail_first = False
                raise TimeoutError("Kafka unavailable after archive")
            return SimpleNamespace(partition=0, offset=self.calls)

        async def stop(self):
            self.stopped += 1

    producers = [FakeProducer(fail_first=True), FakeProducer(fail_first=False)]

    async def create_fake_producer():
        return producers.pop(0)

    monkeypatch.setattr(replay.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(replay, "create_producer", create_fake_producer)
    monkeypatch.setattr(replay_module_publisher(), "session_factory", factory)
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end = datetime(2025, 1, 2, tzinfo=timezone.utc)

    with pytest.raises(TimeoutError):
        await replay.replay_once(start=start, end=end, interval_seconds=0)

    async with factory() as session:
        run = await session.scalar(select(IngestionRun))
        interval = await session.scalar(select(IngestionInterval))
        stored_archive = await session.scalar(select(SourceArchive))
    assert run is not None and run.outcome == "failed"
    assert interval is not None and interval.status == "failed"
    assert stored_archive is not None
    archive_path = Path(stored_archive.storage_path)
    assert archive_path.is_file()
    assert archive_path.parent == archive_dir / stored_archive.sha256[:2]

    published = await replay.replay_once(start=start, end=end, interval_seconds=0)
    assert len(published) == 1
    assert len(requests) == 1
    assert producers == []

    repeated = await replay.replay_once(start=start, end=end, interval_seconds=0)
    assert repeated == []
    assert len(requests) == 1
    assert producers == []

    async with factory() as session:
        successful_run = await session.scalar(
            select(IngestionRun).where(IngestionRun.outcome == "succeeded")
        )
        completed_interval = await session.scalar(
            select(IngestionInterval).where(IngestionInterval.status == "complete")
        )
    assert successful_run is not None
    assert completed_interval is not None


def replay_module_publisher():
    from observatorio.producer import publisher

    return publisher
