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
async def test_live_event_is_persisted_idempotently_with_latest_current_version() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    def message(updated: int) -> bytes:
        return json.dumps(
            {
                "mode": "live",
                "source": "usgs-live",
                "ingestion_run_id": str(uuid4()),
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "id": "live-integration",
                    "properties": {"time": 1_760_000_000_000, "updated": updated, "mag": 5.2},
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
