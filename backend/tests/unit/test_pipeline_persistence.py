from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from observatorio.consumer.main import handle_message
from observatorio.consumer.processor import persist_message
from observatorio.models import (
    Base,
    EventCurrent,
    EventVersion,
    EventVersionSource,
    IngestionRun,
    Quarantine,
)


@pytest_asyncio.fixture
async def database_sessions():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


def _wire_event(
    updated: int,
    *,
    mode: str = "live",
    event_id: str = "test-event",
    magnitude: float | None = 4.1,
) -> bytes:
    envelope = {
        "id": event_id,
        "mode": mode,
        "source": "usgs-test",
        "ingestion_run_id": str(uuid4()),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "type": "Feature",
            "id": event_id,
            "properties": {
                "type": "earthquake",
                "time": 1_760_000_000_000,
                "updated": updated,
                "mag": magnitude,
            },
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
async def test_new_version_is_flushed_before_its_source_with_foreign_keys_enabled() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    message = json.loads(_wire_event(1_760_000_001_000))
    message["payload"]["geometry"]["coordinates"] = [-150.0, 0.0, None]
    outcome = await persist_message(
        factory,
        json.dumps(message).encode(),
        topic="quakes.live",
        partition=0,
        offset=0,
    )

    async with factory() as session:
        version = await session.get(
            EventVersion,
            ("live", "test-event", datetime.fromtimestamp(1_760_000_001_000 / 1000, tz=timezone.utc).replace(tzinfo=None)),
        )
        source = await session.get(
            EventVersionSource,
            ("live", "test-event", datetime.fromtimestamp(1_760_000_001_000 / 1000, tz=timezone.utc).replace(tzinfo=None)),
        )
    await engine.dispose()

    assert outcome == "persisted"
    assert version is not None
    assert source is not None


@pytest.mark.asyncio
async def test_invalid_message_is_quarantined_idempotently(database_sessions) -> None:
    invalid = json.dumps(
        {
            "id": "bad-event",
            "mode": "live",
            "source": "usgs-test",
            "payload": {
                "type": "Feature",
                "id": "bad-event",
                "properties": {
                    "type": "earthquake",
                    "time": 1_760_000_000_000,
                    "updated": 1_760_000_000_000,
                },
                "geometry": {"type": "Point", "coordinates": [200, 95]},
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
async def test_invalid_optional_text_type_is_durably_quarantined(database_sessions) -> None:
    invalid = json.loads(_wire_event(1_760_000_001_000))
    invalid["payload"]["properties"]["place"] = ["not", "text"]
    raw_message = json.dumps(invalid).encode()

    assert await persist_message(
        database_sessions,
        raw_message,
        topic="quakes.live",
        partition=2,
        offset=14,
    ) == "quarantined"

    async with database_sessions() as session:
        rows = (await session.scalars(select(Quarantine))).all()
    assert len(rows) == 1
    assert rows[0].reason_code == "invalid_place"
    assert rows[0].raw_message == raw_message


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


@pytest.mark.asyncio
async def test_exclusion_is_durable_and_idempotent_by_kafka_position(database_sessions) -> None:
    excluded = json.loads(_wire_event(1_760_000_001_000))
    excluded["payload"]["properties"]["type"] = "quarry blast"
    raw_message = json.dumps(excluded).encode()
    async with database_sessions() as session:
        async with session.begin():
            session.add(
                IngestionRun(
                    run_id=UUID(excluded["ingestion_run_id"]),
                    mode="live",
                    source="usgs-test",
                    started_at=datetime.now(timezone.utc),
                    outcome="running",
                )
            )

    assert await persist_message(
        database_sessions,
        raw_message,
        topic="quakes.live",
        partition=0,
        offset=8,
    ) == "quarantined"
    assert await persist_message(
        database_sessions,
        raw_message,
        topic="quakes.live",
        partition=0,
        offset=8,
    ) == "quarantined_duplicate"
    async with database_sessions() as session:
        rows = (await session.scalars(select(Quarantine))).all()
    assert len(rows) == 1
    assert rows[0].reason_code == "event_type_excluded"
    assert rows[0].raw_message == raw_message
    assert rows[0].ingestion_run_id == UUID(excluded["ingestion_run_id"])


@pytest.mark.asyncio
async def test_same_version_changed_payload_replaces_source_and_normalized_fields(database_sessions) -> None:
    updated = 1_760_000_001_000
    assert await persist_message(
        database_sessions,
        _wire_event(updated, magnitude=4.1),
        topic="quakes.live",
        partition=0,
        offset=0,
    ) == "persisted"
    changed = json.loads(_wire_event(updated, magnitude=3.8))
    changed["ingestion_run_id"] = str(uuid4())
    changed["payload"]["properties"]["place"] = "updated place"
    assert await persist_message(
        database_sessions,
        json.dumps(changed).encode(),
        topic="quakes.live",
        partition=0,
        offset=1,
    ) == "replaced"

    async with database_sessions() as session:
        versions = (await session.scalars(select(EventVersion))).all()
        sources = (await session.scalars(select(EventVersionSource))).all()
        quarantines = (await session.scalars(select(Quarantine))).all()
    assert len(versions) == len(sources) == 1
    assert float(versions[0].magnitude) == 3.8
    assert versions[0].place == "updated place"
    assert sources[0].original_feature["properties"]["mag"] == 3.8
    assert sources[0].payload_sha256
    assert sources[0].ingestion_run_id == UUID(changed["ingestion_run_id"])
    assert quarantines == []


@pytest.mark.asyncio
async def test_legacy_version_without_source_accepts_first_complete_feature(database_sessions) -> None:
    updated = 1_760_000_001_000
    await persist_message(
        database_sessions,
        _wire_event(updated),
        topic="quakes.live",
        partition=0,
        offset=0,
    )
    async with database_sessions() as session:
        async with session.begin():
            source = await session.get(
                EventVersionSource,
                ("live", "test-event", datetime.fromtimestamp(updated / 1000, tz=timezone.utc)),
            )
            assert source is not None
            await session.delete(source)

    replacement = _wire_event(updated, magnitude=5.1)
    assert await persist_message(
        database_sessions,
        replacement,
        topic="quakes.live",
        partition=0,
        offset=1,
    ) == "replaced"
    async with database_sessions() as session:
        versions = (await session.scalars(select(EventVersion))).all()
        sources = (await session.scalars(select(EventVersionSource))).all()
    assert len(versions) == len(sources) == 1
    assert sources[0].original_feature["type"] == "Feature"
    assert float(versions[0].magnitude) == 5.1


@pytest.mark.asyncio
async def test_event_and_version_counts_for_duplicate_stale_and_new_event(database_sessions) -> None:
    first = 1_760_000_001_000
    revision = 1_760_000_002_000
    second_event = 1_760_000_003_000

    assert await persist_message(
        database_sessions,
        _wire_event(first, event_id="E1"),
        topic="quakes.live",
        partition=0,
        offset=0,
    ) == "persisted"
    assert await persist_message(
        database_sessions,
        _wire_event(first, event_id="E1"),
        topic="quakes.live",
        partition=0,
        offset=1,
    ) == "duplicate"
    assert await persist_message(
        database_sessions,
        _wire_event(revision, event_id="E1"),
        topic="quakes.live",
        partition=0,
        offset=2,
    ) == "persisted"
    assert await persist_message(
        database_sessions,
        _wire_event(first, event_id="E1"),
        topic="quakes.live",
        partition=0,
        offset=3,
    ) == "duplicate"
    assert await persist_message(
        database_sessions,
        _wire_event(second_event, event_id="E2"),
        topic="quakes.live",
        partition=0,
        offset=4,
    ) == "persisted"

    async with database_sessions() as session:
        versions = (await session.scalars(select(EventVersion))).all()
        currents = (await session.scalars(select(EventCurrent))).all()
        current_e1 = await session.get(EventCurrent, ("live", "E1"))
    assert len(versions) == 3
    assert len(currents) == 2
    assert current_e1 is not None
    assert current_e1.current_updated_at.replace(tzinfo=timezone.utc) == datetime.fromtimestamp(
        revision / 1000,
        tz=timezone.utc,
    )
