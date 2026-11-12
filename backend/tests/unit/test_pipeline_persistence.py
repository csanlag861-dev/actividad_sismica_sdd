from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from observatorio.consumer.main import handle_message
from observatorio.consumer.processor import persist_message
from observatorio.models import Base, EventCurrent, EventVersion, Quarantine


@pytest_asyncio.fixture
async def database_sessions():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


def _wire_event(updated: int, *, mode: str = "live") -> bytes:
    envelope = {
        "id": "test-event",
        "mode": mode,
        "source": "usgs-test",
        "ingestion_run_id": str(uuid4()),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "id": "test-event",
            "properties": {"time": 1_760_000_000_000, "updated": updated, "mag": 4.1},
            "geometry": {"type": "Point", "coordinates": [-100.0, 40.0, 8.0]},
        },
    }
    return json.dumps(envelope).encode()


@pytest.mark.asyncio
async def test_versions_are_idempotent_and_current_never_moves_back(database_sessions) -> None:
    newer = 1_760_000_002_000
    older = 1_760_000_001_000
    assert await persist_message(database_sessions, _wire_event(newer), topic="quakes.live", partition=0, offset=0) == "persisted"
    assert await persist_message(database_sessions, _wire_event(newer), topic="quakes.live", partition=0, offset=1) == "duplicate"
    assert await persist_message(database_sessions, _wire_event(older), topic="quakes.live", partition=0, offset=2) == "persisted"

    async with database_sessions() as session:
        versions = (await session.scalars(select(EventVersion))).all()
        current = await session.get(EventCurrent, ("live", "test-event"))
    assert len(versions) == 2
    assert current is not None
    assert current.current_updated_at == datetime.fromtimestamp(newer / 1000, tz=timezone.utc).replace(tzinfo=None)


@pytest.mark.asyncio
async def test_invalid_message_is_quarantined_idempotently(database_sessions) -> None:
    invalid = json.dumps(
        {
            "id": "bad-event",
            "mode": "live",
            "source": "usgs-test",
            "payload": {
                "id": "bad-event",
                "properties": {"time": 1_760_000_000_000, "updated": 1_760_000_000_000},
                "geometry": {"coordinates": [200, 95]},
            },
        }
    ).encode()

    assert await persist_message(database_sessions, invalid, topic="quakes.live", partition=1, offset=4) == "quarantined"
    assert await persist_message(database_sessions, invalid, topic="quakes.live", partition=1, offset=4) == "quarantined_duplicate"
    async with database_sessions() as session:
        quarantined = (await session.scalars(select(Quarantine))).all()
    assert len(quarantined) == 1
    assert quarantined[0].reason_code == "coordinates_out_of_range"
    assert quarantined[0].raw_message == invalid


@pytest.mark.asyncio
async def test_offset_commit_happens_after_database_persistence(monkeypatch) -> None:
    from observatorio.consumer import main

    calls: list[str] = []

    async def persist(*args, **kwargs):
        calls.append("database")
        return "persisted"

    class FakeConsumer:
        async def commit(self, offsets):
            calls.append("commit")

    monkeypatch.setattr(main, "persist_message", persist)
    msg = SimpleNamespace(value=b"{}", topic="quakes.live", partition=2, offset=9)
    await handle_message(FakeConsumer(), msg)
    assert calls == ["database", "commit"]


@pytest.mark.asyncio
async def test_offset_is_not_committed_when_database_persistence_fails(monkeypatch) -> None:
    from observatorio.consumer import main

    commits: list[str] = []

    async def persist(*args, **kwargs):
        raise ConnectionError("database unavailable")

    class FakeConsumer:
        async def commit(self, offsets):
            commits.append("commit")

    monkeypatch.setattr(main, "persist_message", persist)
    msg = SimpleNamespace(value=b"{}", topic="quakes.live", partition=2, offset=10)
    with pytest.raises(ConnectionError):
        await handle_message(FakeConsumer(), msg)
    assert commits == []
