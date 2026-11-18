from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from observatorio.models import IngestionInterval, IngestionRun
from tests.api_support import seed_api_event


@pytest.mark.asyncio
async def test_postgresql_api_query_health_schema_and_statistics(postgres_api_context) -> None:
    client, factory, _ = postgres_api_context
    now = datetime.now(timezone.utc).replace(microsecond=0)
    await seed_api_event(
        factory,
        event_id="postgres-live",
        event_time=now,
        magnitude=4.0,
    )
    await seed_api_event(
        factory,
        event_id="postgres-replay",
        mode="replay",
        event_time=datetime(2025, 6, 1, tzinfo=timezone.utc),
        updated_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
        magnitude=4.2,
    )
    async with factory() as session:
        replay_run = await session.scalar(
            text("SELECT run_id FROM ingestion_run WHERE mode = 'replay'")
        )
        session.add(
            IngestionInterval(
                run_id=replay_run,
                interval_start=datetime(2025, 1, 1, tzinfo=timezone.utc),
                interval_end=datetime(2026, 1, 1, tzinfo=timezone.utc),
                filters={"min_magnitude": 4.0, "event_type": "earthquake"},
                status="complete",
                records_received=1,
                unique_versions=1,
                published_count=1,
            )
        )
        await session.commit()

    health = await client.get("/api/salud")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    async with factory() as session:
        await session.execute(text("DELETE FROM alembic_version"))
        await session.commit()
    unavailable = await client.get("/api/salud")
    assert unavailable.status_code == 503
    assert unavailable.json() == {"status": "unavailable", "last_ingestion": None}

    async with factory() as session:
        await session.execute(
            text(
                "INSERT INTO alembic_version (version_num) "
                "VALUES ('0007_event_time_query_index')"
            )
        )
        await session.commit()
    assert (await client.get("/api/salud")).status_code == 200

    start = now - timedelta(minutes=1)
    end = now + timedelta(minutes=1)
    events = await client.get(
        "/api/eventos",
        params={"start": start.isoformat(), "end": end.isoformat(), "min_mag": "4"},
    )
    assert events.status_code == 200
    assert [feature["id"] for feature in events.json()["features"]] == ["postgres-live"]

    statistics = await client.get(
        "/api/estadisticas",
        params={"start": start.isoformat(), "end": end.isoformat(), "min_mag": "4"},
    )
    assert statistics.status_code == 200
    assert statistics.json()["historical_comparison"]["baseline_available"] is True
    assert statistics.json()["distributions"]["magnitude"]["valid_count"] == 1
