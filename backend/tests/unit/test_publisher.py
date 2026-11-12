from __future__ import annotations

from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from observatorio.models import Base, PublishedVersion
from observatorio.producer.publisher import publish_event


@pytest.mark.asyncio
async def test_publication_is_recorded_after_ack_and_duplicate_is_skipped() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    class FakeProducer:
        calls = 0

        async def send_and_wait(self, topic, *, value, key):
            self.calls += 1
            return SimpleNamespace(partition=0, offset=self.calls - 1)

    producer = FakeProducer()
    payload = {
        "id": "evt-ack",
        "source": "usgs-live",
        "properties": {"updated": 1_760_000_000_000},
        "geometry": {"coordinates": [0, 0, 1]},
    }

    first = await publish_event(
        producer,
        "quakes.live",
        payload,
        ingestion_run_id="02dfad0c-2c13-431c-95fb-4bdb4d253e23",
        session_factory_override=factory,
    )
    second = await publish_event(producer, "quakes.live", payload, session_factory_override=factory)
    async with factory() as session:
        rows = (await session.scalars(select(PublishedVersion))).all()
    await engine.dispose()

    assert first["status"] == "published"
    assert second["status"] == "already_published"
    assert producer.calls == 1
    assert len(rows) == 1
    assert rows[0].kafka_offset == 0


@pytest.mark.asyncio
async def test_failed_kafka_ack_does_not_record_a_publication() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    class FailedProducer:
        async def send_and_wait(self, topic, *, value, key):
            raise TimeoutError("Kafka did not acknowledge")

    with pytest.raises(TimeoutError):
        await publish_event(
            FailedProducer(),
            "quakes.live",
            {
                "id": "evt-no-ack",
                "properties": {"updated": 1_760_000_000_000},
                "geometry": {"coordinates": [0, 0, 1]},
            },
            session_factory_override=factory,
        )
    async with factory() as session:
        rows = (await session.scalars(select(PublishedVersion))).all()
    await engine.dispose()
    assert rows == []
