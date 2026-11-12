from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from observatorio.consumer.processor import persist_message
from observatorio.models import Base, EventCurrent, EventVersion


@pytest.mark.asyncio
async def test_replay_events_are_isolated_from_live_rows() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    def message(mode: str) -> bytes:
        return json.dumps(
            {
                "mode": mode,
                "source": f"usgs-{mode}",
                "ingestion_run_id": str(uuid4()),
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "id": "shared-event-id",
                    "properties": {"time": 1_760_000_000_000, "updated": 1_760_000_000_000},
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
