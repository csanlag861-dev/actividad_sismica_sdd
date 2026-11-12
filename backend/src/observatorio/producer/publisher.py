from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from observatorio.db.session import session_factory
from observatorio.models import PublishedVersion


def _event_updated_at(payload: Mapping[str, Any]) -> datetime:
    event = payload.get("payload", payload)
    properties = event.get("properties", {}) if isinstance(event, Mapping) else {}
    value = properties.get("updated")
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, (int, float)):
        parsed = datetime.fromtimestamp(value / 1000, tz=timezone.utc)
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError("USGS event is missing its updated timestamp")
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


async def publish_event(
    producer: Any,
    topic: str,
    payload: Mapping[str, Any],
    *,
    mode: str = "live",
    key: str | None = None,
    ingestion_run_id: UUID | str | None = None,
    session_factory_override: async_sessionmaker[AsyncSession] | None = None,
) -> dict[str, Any]:
    if mode not in {"live", "replay"}:
        raise ValueError("mode must be live or replay")
    if not isinstance(payload, Mapping):
        raise TypeError("event payload must be a mapping")

    raw_event = payload.get("payload", payload)
    if not isinstance(raw_event, Mapping):
        raise TypeError("event payload must contain a mapping")
    event_id = str(raw_event.get("id") or payload.get("event_id") or key or "")
    if not event_id:
        raise ValueError("event payload is missing its id")
    updated_at = _event_updated_at(payload)
    factory = session_factory_override or session_factory

    async with factory() as session:
        latest = await session.scalar(
            select(func.max(PublishedVersion.updated_at)).where(
                PublishedVersion.mode == mode,
                PublishedVersion.event_id == event_id,
            )
        )
    if latest is not None:
        if latest.tzinfo is None:
            latest = latest.replace(tzinfo=timezone.utc)
        if latest >= updated_at:
            return {"event_id": event_id, "mode": mode, "status": "already_published"}

    now = datetime.now(timezone.utc)
    run_id = str(ingestion_run_id or payload.get("ingestion_run_id") or "")
    envelope = {
        "id": event_id,
        "mode": mode,
        "source": payload.get("source", "usgs"),
        "ingestion_run_id": run_id,
        "ingested_at": now.isoformat(),
        "published_at": now.isoformat(),
        "payload": dict(raw_event),
    }
    metadata = await producer.send_and_wait(
        topic,
        value=json.dumps(envelope, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        key=event_id.encode("utf-8"),
    )

    async with factory() as session:
        async with session.begin():
            published = PublishedVersion(
                mode=mode,
                event_id=event_id,
                updated_at=updated_at,
                published_at=now,
                kafka_topic=topic,
                kafka_partition=metadata.partition,
                kafka_offset=metadata.offset,
            )
            session.add(published)
    return {
        "topic": topic,
        "partition": metadata.partition,
        "offset": metadata.offset,
        "event_id": event_id,
        "updated_at": updated_at,
        "mode": mode,
        "status": "published",
    }
