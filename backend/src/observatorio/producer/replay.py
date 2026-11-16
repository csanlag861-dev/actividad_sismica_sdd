from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from observatorio.config import settings
from observatorio.db.session import session_factory
from observatorio.kafka import create_producer
from observatorio.logging import get_logger
from observatorio.models import IngestionInterval, IngestionRun, SourceArchive
from observatorio.producer.archive import archive_response
from observatorio.producer.publisher import publish_event
from observatorio.producer.replay_source import (
    PAGE_SIZE,
    USGS_CATALOG_URL,
    ReplayResponse,
    _month_intervals,
    _validate_query,
    fetch_interval_response,
    split_interval,
)
from observatorio.producer.source import safe_source_url

logger = get_logger("observatorio.producer.replay")
SessionFactory = async_sessionmaker[AsyncSession]


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay historical USGS earthquakes into the isolated replay topic")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--min-magnitude", type=float, default=4.0)
    parser.add_argument("--event-type", default="earthquake")
    parser.add_argument("--interval-seconds", type=float, default=settings.replay_interval_seconds)
    parser.add_argument("--start", type=_parse_utc, help="inclusive UTC start timestamp (ISO 8601)")
    parser.add_argument("--end", type=_parse_utc, help="exclusive UTC end timestamp (ISO 8601)")
    return parser.parse_args()


async def _find_or_create_run(
    factory: SessionFactory,
    *,
    source_label: str,
    query_filters: dict[str, Any],
    started_at: datetime,
    start: datetime,
    end: datetime,
) -> tuple[UUID, bool]:
    async with factory() as session:
        candidates = (
            await session.scalars(
                select(IngestionRun)
                .where(
                    IngestionRun.mode == "replay",
                    IngestionRun.source == source_label,
                    IngestionRun.outcome.in_(("running", "failed", "succeeded")),
                )
                .order_by(IngestionRun.started_at.desc())
            )
        ).all()
        matching_complete_id: UUID | None = None
        for candidate in candidates:
            metadata = candidate.query_metadata or {}
            if metadata.get("filters") != query_filters:
                continue
            intervals = (
                await session.scalars(
                    select(IngestionInterval).where(
                        IngestionInterval.run_id == candidate.run_id
                    )
                )
            ).all()
            if intervals and all(interval.status == "complete" for interval in intervals):
                if candidate.outcome == "succeeded":
                    matching_complete_id = candidate.run_id
                    break
                continue
            candidate.outcome = "running"
            candidate.finished_at = None
            candidate.error_code = None
            candidate.error_summary = None
            await session.commit()
            return candidate.run_id, False
        if matching_complete_id is not None:
            return matching_complete_id, True

    run_id = uuid4()
    async with factory() as session:
        async with session.begin():
            session.add(
                IngestionRun(
                    run_id=run_id,
                    mode="replay",
                    source=source_label,
                    started_at=started_at,
                    outcome="running",
                    request_start=start,
                    request_end=end,
                    query_metadata={"filters": query_filters},
                )
            )
    return run_id, False


async def _get_or_create_interval(
    factory: SessionFactory,
    *,
    run_id: UUID,
    interval_start: datetime,
    interval_end: datetime,
    filters: dict[str, Any],
) -> IngestionInterval:
    async with factory() as session:
        async with session.begin():
            interval = await session.scalar(
                select(IngestionInterval).where(
                    IngestionInterval.run_id == run_id,
                    IngestionInterval.interval_start == interval_start,
                    IngestionInterval.interval_end == interval_end,
                )
            )
            if interval is None:
                interval = IngestionInterval(
                    run_id=run_id,
                    interval_start=interval_start,
                    interval_end=interval_end,
                    filters=filters,
                    status="pending",
                )
                session.add(interval)
                await session.flush()
            return interval


async def _load_archived_response(
    factory: SessionFactory,
    interval_id: int,
) -> ReplayResponse | None:
    async with factory() as session:
        interval = await session.get(IngestionInterval, interval_id)
        if interval is None or interval.source_archive_sha256 is None:
            return None
        archive = await session.get(SourceArchive, interval.source_archive_sha256)
        if archive is None or archive.deleted_at is not None:
            raise FileNotFoundError(
                f"archive reference is unavailable for interval {interval_id}"
            )
        path = Path(archive.storage_path)
        content = await asyncio.to_thread(path.read_bytes)
        digest = hashlib.sha256(content).hexdigest()
        if digest != interval.source_archive_sha256:
            raise ValueError(f"archive checksum mismatch for interval {interval_id}")
        try:
            payload = json.loads(content)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"archived response is invalid JSON for interval {interval_id}") from exc
        if (
            not isinstance(payload, dict)
            or payload.get("type") != "FeatureCollection"
            or not isinstance(payload.get("features"), list)
            or any(not isinstance(feature, dict) for feature in payload["features"])
        ):
            raise ValueError(f"archived response is not a GeoJSON FeatureCollection for interval {interval_id}")
        return ReplayResponse(
            interval_start=interval.interval_start,
            interval_end=interval.interval_end,
            params={
                str(key): str(value)
                for key, value in (interval.filters or {}).items()
            },
            url=interval.request_url or USGS_CATALOG_URL,
            status_code=interval.http_status or 200,
            content=content,
            payload=payload,
            requested_at=interval.requested_at or interval.interval_start,
            received_at=interval.archived_at or interval.interval_start,
            attempts=interval.attempt_count,
        )


async def _update_interval(
    factory: SessionFactory,
    interval_id: int,
    **updates: Any,
) -> None:
    async with factory() as session:
        async with session.begin():
            interval = await session.get(IngestionInterval, interval_id)
            if interval is None:
                raise LookupError(f"ingestion interval disappeared: {interval_id}")
            for name, value in updates.items():
                setattr(interval, name, value)


async def _mark_interval_failed(
    factory: SessionFactory,
    interval_id: int,
    exc: Exception,
) -> None:
    await _update_interval(
        factory,
        interval_id,
        status="failed",
        error_summary=type(exc).__name__,
    )


def _unique_versions(features: list[dict[str, Any]]) -> int:
    identities: set[tuple[str, str]] = set()
    for feature in features:
        properties = feature.get("properties") or {}
        event_id = feature.get("id")
        updated_at = properties.get("updated")
        if event_id is not None and updated_at is not None:
            identities.add((str(event_id), str(updated_at)))
    return len(identities)


def _remember_unique_versions(
    features: list[dict[str, Any]],
    identities: set[tuple[str, str]],
) -> None:
    for feature in features:
        properties = feature.get("properties") or {}
        event_id = feature.get("id")
        updated_at = properties.get("updated")
        if event_id is not None and updated_at is not None:
            identities.add((str(event_id), str(updated_at)))


async def _publish_interval_features(
    factory: SessionFactory,
    response: ReplayResponse,
    *,
    producer_state: dict[str, Any],
    run_id: UUID,
    interval_seconds: float,
    published: list[dict],
    pacing: dict[str, bool],
) -> int:
    processed = 0
    for feature in response.features:
        if pacing["has_previous"] and interval_seconds > 0:
            await asyncio.sleep(interval_seconds)
        if producer_state["producer"] is None:
            producer_state["producer"] = await create_producer()
        result = await publish_event(
            producer_state["producer"],
            "quakes.replay",
            {
                "payload": feature,
                "source": "usgs-replay",
                "ingestion_run_id": str(run_id),
                "ingested_at": response.received_at.isoformat(),
            },
            mode="replay",
            key=str(feature.get("id") or ""),
            ingestion_run_id=run_id,
            session_factory_override=factory,
        )
        pacing["has_previous"] = True
        processed += 1
        if result["status"] == "published":
            published.append(result)
    return processed


async def _process_interval(
    factory: SessionFactory,
    client: httpx.AsyncClient,
    *,
    run_id: UUID,
    interval_start: datetime,
    interval_end: datetime,
    filters: dict[str, Any],
    min_magnitude: float,
    event_type: str,
    url: str,
    producer_state: dict[str, Any],
    interval_seconds: float,
    published: list[dict],
    pacing: dict[str, bool],
    unique_identities: set[tuple[str, str]],
) -> tuple[int, int, int]:
    interval = await _get_or_create_interval(
        factory,
        run_id=run_id,
        interval_start=interval_start,
        interval_end=interval_end,
        filters=filters,
    )
    was_complete = interval.status == "complete"
    interval_id = interval.interval_id
    try:
        response = await _load_archived_response(factory, interval_id)
        if was_complete and response is None:
            raise FileNotFoundError(f"completed interval {interval_id} has no source archive")
        if response is None:
            now = datetime.now(timezone.utc)
            await _update_interval(
                factory,
                interval_id,
                status="pending",
                attempt_count=interval.attempt_count + 1,
                requested_at=now,
                request_url=safe_source_url(url),
                error_summary=None,
            )
            response = await fetch_interval_response(
                client,
                interval_start=interval_start,
                interval_end=interval_end,
                min_magnitude=min_magnitude,
                event_type=event_type,
                url=url,
            )
            archive = await archive_response(
                response.content,
                source="usgs-replay",
                ingestion_interval_id=interval_id,
                session_factory_override=factory,
            )
            await _update_interval(
                factory,
                interval_id,
                status="archived",
                attempt_count=interval.attempt_count + response.attempts,
                request_url=safe_source_url(response.url),
                http_status=response.status_code,
                records_received=len(response.features),
                unique_versions=_unique_versions(response.features),
                archived_at=response.received_at,
                error_summary=None,
            )
            logger.info(
                "Archived replay interval %s–%s (%s features, sha256=%s)",
                interval_start.isoformat(),
                interval_end.isoformat(),
                len(response.features),
                archive.sha256,
            )

        if len(response.features) >= PAGE_SIZE:
            midpoint, right_start = split_interval(interval_start, interval_end)
            if not was_complete:
                await _update_interval(
                    factory,
                    interval_id,
                    status="archived",
                    records_received=len(response.features),
                )
            left = await _process_interval(
                factory,
                client,
                run_id=run_id,
                interval_start=interval_start,
                interval_end=midpoint,
                filters=filters,
                min_magnitude=min_magnitude,
                event_type=event_type,
                url=url,
                producer_state=producer_state,
                interval_seconds=interval_seconds,
                published=published,
                pacing=pacing,
                unique_identities=unique_identities,
            )
            right = await _process_interval(
                factory,
                client,
                run_id=run_id,
                interval_start=right_start,
                interval_end=interval_end,
                filters=filters,
                min_magnitude=min_magnitude,
                event_type=event_type,
                url=url,
                producer_state=producer_state,
                interval_seconds=interval_seconds,
                published=published,
                pacing=pacing,
                unique_identities=unique_identities,
            )
            unique_count = left[0] + right[0]
            record_count = left[1] + right[1] + len(response.features)
            processed_count = left[2] + right[2]
            if was_complete:
                return unique_count, record_count, processed_count
            await _update_interval(
                factory,
                interval_id,
                status="complete",
                unique_versions=unique_count,
                records_received=len(response.features),
                published_count=processed_count,
                completed_at=datetime.now(timezone.utc),
            )
            return unique_count, record_count, processed_count

        if was_complete:
            _remember_unique_versions(response.features, unique_identities)
            return interval.unique_versions, interval.records_received, interval.published_count

        _remember_unique_versions(response.features, unique_identities)
        if response.features:
            await _update_interval(
                factory,
                interval_id,
                status="publishing",
                publishing_at=datetime.now(timezone.utc),
            )
            processed_count = await _publish_interval_features(
                factory,
                response,
                producer_state=producer_state,
                run_id=run_id,
                interval_seconds=interval_seconds,
                published=published,
                pacing=pacing,
            )
        else:
            processed_count = 0

        await _update_interval(
            factory,
            interval_id,
            status="complete",
            records_received=len(response.features),
            unique_versions=_unique_versions(response.features),
            published_count=processed_count,
            completed_at=datetime.now(timezone.utc),
            error_summary=None,
        )
        return _unique_versions(response.features), len(response.features), processed_count
    except Exception as exc:
        await _mark_interval_failed(factory, interval_id, exc)
        raise


async def replay_once(
    *,
    year: int = 2025,
    min_magnitude: float = 4.0,
    event_type: str = "earthquake",
    interval_seconds: float = 0.0,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[dict]:
    if min_magnitude < -2:
        raise ValueError("min_magnitude is outside the USGS-supported range")
    if not event_type.strip():
        raise ValueError("event_type cannot be empty")
    range_start, range_end = _validate_query(
        year=year,
        min_magnitude=min_magnitude,
        event_type=event_type,
        start=start,
        end=end,
    )
    intervals = _month_intervals(range_start, range_end)
    query_filters = {
        "year": year if start is None else None,
        "start_utc": range_start.isoformat(),
        "end_utc": range_end.isoformat(),
        "min_magnitude": min_magnitude,
        "event_type": event_type,
        "extent": "global",
        "order_by": "time-asc",
    }
    source_label = f"{safe_source_url(USGS_CATALOG_URL)}:historical"
    started_at = datetime.now(timezone.utc)
    factory = session_factory
    run_id, already_complete = await _find_or_create_run(
        factory,
        source_label=source_label,
        query_filters=query_filters,
        started_at=started_at,
        start=range_start,
        end=range_end,
    )
    if already_complete:
        logger.info("Historical query already has complete checkpoints; no replay was needed")
        return []

    published: list[dict] = []
    producer_state: dict[str, Any] = {"producer": None}
    aggregates = {"records_received": 0, "unique_versions": 0, "processed_count": 0}
    unique_identities: set[tuple[str, str]] = set()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for interval_start, interval_end in intervals:
                counts = await _process_interval(
                    factory,
                    client,
                    run_id=run_id,
                    interval_start=interval_start,
                    interval_end=interval_end,
                    filters=query_filters,
                    min_magnitude=min_magnitude,
                    event_type=event_type,
                    url=USGS_CATALOG_URL,
                    producer_state=producer_state,
                    interval_seconds=interval_seconds,
                    published=published,
                    pacing={"has_previous": False},
                    unique_identities=unique_identities,
                )
                aggregates["unique_versions"] += counts[0]
                aggregates["records_received"] += counts[1]
                aggregates["processed_count"] += counts[2]
        aggregates["unique_versions"] = len(unique_identities)
        producer = producer_state.pop("producer")
        if producer is not None:
            await producer.stop()
        finished_at = datetime.now(timezone.utc)
        async with factory() as session:
            async with session.begin():
                run = await session.get(IngestionRun, run_id)
                if run is None:
                    raise LookupError(f"ingestion run disappeared: {run_id}")
                run.outcome = "succeeded"
                run.finished_at = finished_at
                run.request_start = range_start
                run.request_end = range_end
                run.query_metadata = {
                    "filters": query_filters,
                    **aggregates,
                    "published_messages": len(published),
                }
                run.records_received = aggregates["records_received"]
                run.http_status = 200
        return published
    except asyncio.CancelledError:
        producer = producer_state.pop("producer", None)
        if producer is not None:
            try:
                await producer.stop()
            except Exception as stop_error:
                logger.error("Kafka producer shutdown failed: %s", type(stop_error).__name__)
        async with factory() as session:
            async with session.begin():
                run = await session.get(IngestionRun, run_id)
                if run is not None:
                    run.outcome = "failed"
                    run.finished_at = datetime.now(timezone.utc)
                    run.error_code = "CancelledError"
                    run.error_summary = "Historical replay was cancelled; checkpoints were retained"
        raise
    except Exception as exc:
        producer = producer_state.pop("producer", None)
        if producer is not None:
            try:
                await producer.stop()
            except Exception as stop_error:
                logger.error("Kafka producer shutdown failed: %s", type(stop_error).__name__)
        failed_at = datetime.now(timezone.utc)
        async with factory() as session:
            async with session.begin():
                run = await session.get(IngestionRun, run_id)
                if run is not None:
                    run.outcome = "failed"
                    run.finished_at = failed_at
                    run.error_code = type(exc).__name__
                    run.error_summary = "Historical interval failed; completed checkpoints were retained"
        logger.error("Historical USGS replay failed: %s", type(exc).__name__)
        raise


async def main_async() -> None:
    args = _parse_args()
    if (args.start is None) != (args.end is None):
        raise ValueError("--start and --end must be provided together")
    result = await replay_once(
        year=args.year,
        min_magnitude=args.min_magnitude,
        event_type=args.event_type,
        interval_seconds=args.interval_seconds,
        start=args.start,
        end=args.end,
    )
    logger.info("Published %s replay messages", len(result))
    if not result:
        logger.info("No new replay messages required publication")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
