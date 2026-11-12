from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from observatorio.consumer.geography import country_for_coordinates
from observatorio.consumer.validation import normalize_event
from observatorio.logging import get_logger
from observatorio.models import CalendarDate, EventCurrent, EventVersion, IngestionRun, Quarantine

logger = get_logger("observatorio.consumer.processor")


def process_event(raw_event: dict) -> dict:
    if not isinstance(raw_event, dict):
        raise ValueError("event payload must be a mapping")
    properties = raw_event.get("properties") or {}
    geometry = raw_event.get("geometry") or {}
    coords = geometry.get("coordinates") or [None, None, None]
    return {
        "longitude": coords[0] if len(coords) > 0 else None,
        "latitude": coords[1] if len(coords) > 1 else None,
        "depth_km": coords[2] if len(coords) > 2 else None,
        "magnitude": properties.get("mag"),
        "place": properties.get("place"),
        "event_id": raw_event.get("id"),
        "updated_at": properties.get("updated"),
    }


async def _quarantine(
    session: AsyncSession,
    *,
    raw_message: bytes,
    topic: str,
    partition: int,
    offset: int,
    reason: str,
    parsed_payload: dict[str, Any] | None,
    mode: str,
) -> str:
    existing = await session.scalar(
        select(Quarantine.quarantine_id).where(
            Quarantine.kafka_topic == topic,
            Quarantine.kafka_partition == partition,
            Quarantine.kafka_offset == offset,
        )
    )
    if existing is not None:
        return "quarantined_duplicate"

    event_id = None
    source = "unknown"
    if parsed_payload:
        payload = parsed_payload.get("payload", parsed_payload)
        if isinstance(payload, dict):
            event_id = payload.get("id")
            source = str(parsed_payload.get("source") or payload.get("source") or source)
    session.add(
        Quarantine(
            quarantine_id=uuid4(),
            mode=mode,
            source=source,
            event_id=str(event_id) if event_id is not None else None,
            received_at=datetime.now(timezone.utc),
            reason_code=reason,
            reason_detail=reason,
            kafka_topic=topic,
            kafka_partition=partition,
            kafka_offset=offset,
            raw_message=raw_message,
            parsed_payload=parsed_payload,
        )
    )
    return "quarantined"


async def persist_message(
    session_factory: async_sessionmaker[AsyncSession],
    raw_message: bytes,
    *,
    topic: str,
    partition: int,
    offset: int,
) -> str:
    try:
        message = json.loads(raw_message.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        message = None

    valid, reason, event = normalize_event(message)
    async with session_factory() as session:
        async with session.begin():
            if not valid:
                mode = "replay" if topic.endswith(".replay") else "live"
                outcome = await _quarantine(
                    session,
                    raw_message=raw_message,
                    topic=topic,
                    partition=partition,
                    offset=offset,
                    reason=reason or "invalid_event",
                    parsed_payload=message if isinstance(message, dict) else None,
                    mode=mode,
                )
                return outcome

            version_key = (event["mode"], event["event_id"], event["updated_at"])
            existing_version = await session.get(EventVersion, version_key)
            if existing_version is not None:
                return "duplicate"

            run = await session.get(IngestionRun, event["ingestion_run_id"])
            if run is None:
                run = IngestionRun(
                    run_id=event["ingestion_run_id"],
                    mode=event["mode"],
                    source=event["source"],
                    started_at=event["ingested_at"],
                    outcome="running",
                )
                session.add(run)

            date_utc = event["event_time"].date()
            if await session.get(CalendarDate, date_utc) is None:
                session.add(CalendarDate(date_utc=date_utc))

            country_id = country_for_coordinates(event["longitude"], event["latitude"])
            session.add(
                EventVersion(
                    **event,
                    country_id=country_id,
                    date_utc=date_utc,
                )
            )
            await session.flush()

            current_key = (event["mode"], event["event_id"])
            current = await session.get(EventCurrent, current_key)
            if current is None:
                session.add(
                    EventCurrent(
                        mode=event["mode"],
                        event_id=event["event_id"],
                        current_updated_at=event["updated_at"],
                    )
                )
            else:
                current_updated_at = current.current_updated_at
                if current_updated_at.tzinfo is None:
                    current_updated_at = current_updated_at.replace(tzinfo=timezone.utc)
                if event["updated_at"] > current_updated_at:
                    current.current_updated_at = event["updated_at"]
            return "persisted"
