from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from observatorio.config import settings
from observatorio.db.session import session_factory
from observatorio.kafka import create_producer
from observatorio.logging import get_logger
from observatorio.models import IngestionRun
from observatorio.producer.publisher import publish_event
from observatorio.producer.source import extract_features, fetch_recent_feed

logger = get_logger("observatorio.producer.live")


async def tick_once() -> list[dict]:
    run_id = uuid4()
    request_start = datetime.now(timezone.utc)
    run = IngestionRun(
        run_id=run_id,
        mode="live",
        source="usgs-live",
        started_at=request_start,
        outcome="running",
    )
    async with session_factory() as session:
        async with session.begin():
            session.add(run)

    try:
        payload = await fetch_recent_feed(settings.usgs_url)
    except Exception as exc:
        async with session_factory() as session:
            async with session.begin():
                failed_run = await session.get(IngestionRun, run_id)
                if failed_run is not None:
                    failed_run.outcome = "failed"
                    failed_run.finished_at = datetime.now(timezone.utc)
                    failed_run.request_start = request_start
                    failed_run.request_end = failed_run.finished_at
                    failed_run.error_code = type(exc).__name__
                    failed_run.error_summary = "USGS request failed after retries"
        logger.error("USGS feed request failed for %s: %s", settings.usgs_url, type(exc).__name__)
        raise

    features = extract_features(payload)
    request_end = datetime.now(timezone.utc)
    async with session_factory() as session:
        async with session.begin():
            successful_run = await session.get(IngestionRun, run_id)
            if successful_run is not None:
                successful_run.outcome = "succeeded"
                successful_run.finished_at = request_end
                successful_run.request_start = request_start
                successful_run.request_end = request_end
                successful_run.http_status = 200
                successful_run.records_received = len(features)

    logger.info("Fetched %s earthquake features from %s", len(features), settings.usgs_url)
    published: list[dict] = []
    if not features:
        return published

    producer = await create_producer()
    try:
        for feature in features:
            props = feature.get("properties") or {}
            event_payload = {
                "id": feature.get("id"),
                "properties": props,
                "geometry": feature.get("geometry"),
                "source": "usgs-live",
            }
            result = await publish_event(
                producer,
                "quakes.live",
                event_payload,
                mode="live",
                key=str(feature.get("id") or ""),
                ingestion_run_id=run_id,
            )
            if result["status"] == "published":
                published.append(result)
    finally:
        await producer.stop()
    return published


async def run_loop() -> None:
    retry_delay = 1.0
    while True:
        try:
            await tick_once()
            retry_delay = 1.0
            await asyncio.sleep(settings.poll_seconds)
        except Exception as exc:  # pragma: no cover - runtime guard
            logger.warning("Producer iteration failed; retrying in %.1fs: %s", retry_delay, type(exc).__name__)
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30.0)


def main() -> None:
    asyncio.run(run_loop())


if __name__ == "__main__":
    main()
