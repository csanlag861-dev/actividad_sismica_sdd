from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from observatorio.models import (
    CalendarDate,
    Country,
    EventCurrent,
    EventVersion,
    IngestionRun,
)


async def seed_api_event(
    factory,
    *,
    event_id: str,
    mode: str = "live",
    event_time: datetime | None = None,
    updated_at: datetime | None = None,
    magnitude: float | None = 4.0,
    depth_km: float | None = 10.0,
    country_id: str | None = "ESP",
    current: bool = True,
):
    event_time = event_time or datetime(2026, 11, 17, 12, tzinfo=timezone.utc)
    updated_at = updated_at or event_time
    run_id = uuid4()
    async with factory() as session:
        if country_id is not None and await session.get(Country, country_id) is None:
            session.add(Country(country_id=country_id, country_name="España"))
        if await session.get(CalendarDate, event_time.date()) is None:
            session.add(CalendarDate(date_utc=event_time.date()))
        session.add(
            IngestionRun(
                run_id=run_id,
                mode=mode,
                source="usgs-live" if mode == "live" else "usgs-replay",
                started_at=updated_at,
                finished_at=updated_at,
                outcome="succeeded",
                request_end=updated_at,
                records_received=1,
            )
        )
        await session.flush()
        version = EventVersion(
            mode=mode,
            event_id=event_id,
            updated_at=updated_at,
            event_time=event_time,
            magnitude=magnitude,
            mag_type="ml",
            place="Test location",
            longitude=-3.7,
            latitude=40.4,
            depth_km=depth_km,
            country_id=country_id,
            date_utc=event_time.date(),
            source="usgs-live" if mode == "live" else "usgs-replay",
            ingested_at=updated_at,
            ingestion_run_id=run_id,
            original_payload={},
        )
        session.add(version)
        await session.flush()
        if current:
            session.add(
                EventCurrent(
                    mode=mode,
                    event_id=event_id,
                    current_updated_at=updated_at,
                )
            )
        await session.commit()
        return version
