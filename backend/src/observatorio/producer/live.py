from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from uuid import UUID, uuid4

from observatorio.config import settings
from observatorio.db.session import session_factory
from observatorio.kafka import create_producer
from observatorio.logging import get_logger
from observatorio.models import IngestionRun
from observatorio.producer.archive import archive_response
from observatorio.producer.publisher import publish_event
from observatorio.producer.source import (
    extract_features,
    fetch_recent_response,
    safe_source_url,
)

logger = get_logger("observatorio.producer.live")


async def _finish_run(
    run_id: UUID,
    *,
    outcome: str,
    finished_at: datetime,
    error_code: str | None = None,
    error_summary: str | None = None,
) -> None:
    async with session_factory() as session:
        async with session.begin():
            run = await session.get(IngestionRun, run_id)
            if run is None:
                raise LookupError(f"ingestion run disappeared: {run_id}")
            run.outcome = outcome
            run.finished_at = finished_at
            if error_code is not None:
                run.error_code = error_code
            if error_summary is not None:
                run.error_summary = error_summary


async def tick_once() -> list[dict]:
    run_id = uuid4()
    started_at = datetime.now(timezone.utc)
    safe_url = safe_source_url(settings.usgs_url)
    run = IngestionRun(
        run_id=run_id,
        mode="live",
        source="usgs-live",
        started_at=started_at,
        outcome="running",
        query_metadata={
            "request_url": safe_url,
            "timeout_seconds": settings.usgs_timeout_seconds,
            "source_mode": "live",
        },
    )
    async with session_factory() as session:
        async with session.begin():
            session.add(run)

    try:
        response = await fetch_recent_response(
            settings.usgs_url,
            timeout=settings.usgs_timeout_seconds,
        )
        archived = await archive_response(
            response.content,
            source="usgs-live",
            ingestion_run_id=run_id,
            session_factory_override=session_factory,
        )
        features = extract_features(response.payload)
        async with session_factory() as session:
            async with session.begin():
                persisted_run = await session.get(IngestionRun, run_id)
                if persisted_run is None:
                    raise LookupError(f"ingestion run disappeared: {run_id}")
                persisted_run.request_start = response.requested_at
                persisted_run.request_end = response.received_at
                persisted_run.http_status = response.status_code
                persisted_run.records_received = len(features)
                persisted_run.query_metadata = {
                    **(persisted_run.query_metadata or {}),
                    "request_url": safe_source_url(response.url),
                    "attempts": response.attempts,
                    "response_sha256": archived.sha256,
                    "response_bytes": archived.size_bytes,
                }

        published: list[dict] = []
        if features:
            producer = await create_producer()
            try:
                for feature in features:
                    result = await publish_event(
                        producer,
                        "quakes.live",
                        {
                            "payload": feature,
                            "source": "usgs-live",
                            "ingestion_run_id": str(run_id),
                            "ingested_at": response.received_at.isoformat(),
                        },
                        mode="live",
                        key=str(feature.get("id") or ""),
                        ingestion_run_id=run_id,
                        session_factory_override=session_factory,
                    )
                    if result["status"] == "published":
                        published.append(result)
            finally:
                await producer.stop()

        await _finish_run(
            run_id,
            outcome="succeeded",
            finished_at=datetime.now(timezone.utc),
        )
        logger.info(
            "Archived live response %s with %s features; %s publications acknowledged",
            archived.sha256,
            len(features),
            len(published),
        )
        return published
    except Exception as exc:
        failed_at = datetime.now(timezone.utc)
        await _finish_run(
            run_id,
            outcome="failed",
            finished_at=failed_at,
            error_code=type(exc).__name__,
            error_summary="USGS live ingestion failed; the prior successful run was retained",
        )
        logger.error("USGS live ingestion failed: %s", type(exc).__name__)
        raise


async def run_loop(
    *,
    tick: Callable[[], Awaitable[list[dict]]] = tick_once,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> None:
    period = float(settings.poll_seconds)
    tolerance = settings.poll_tolerance_seconds
    deadline = monotonic()

    while True:
        now = monotonic()
        if now < deadline:
            await sleep(deadline - now)
            now = monotonic()
        if now - deadline > tolerance:
            missed = int((now - deadline - tolerance) // period) + 1
            logger.warning("Skipped %s missed live polling deadline(s)", missed)
            deadline += missed * period
            continue

        try:
            await tick()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - runtime guard
            logger.warning("Live polling cycle failed: %s", type(exc).__name__)

        deadline += period
        now = monotonic()
        if now - deadline > tolerance:
            missed = int((now - deadline - tolerance) // period) + 1
            logger.warning("Skipped %s missed live polling deadline(s)", missed)
            deadline += missed * period


def main() -> None:
    asyncio.run(run_loop())


if __name__ == "__main__":
    main()
