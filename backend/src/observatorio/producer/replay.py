from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from observatorio.config import settings
from observatorio.db.session import session_factory
from observatorio.kafka import create_producer
from observatorio.logging import get_logger
from observatorio.models import IngestionRun
from observatorio.producer.publisher import publish_event
from observatorio.producer.replay_source import USGS_CATALOG_URL, fetch_replay_events

logger = get_logger("observatorio.producer.replay")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay historical USGS earthquakes into the isolated replay topic")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--min-magnitude", type=float, default=4.0)
    parser.add_argument("--event-type", default="earthquake")
    parser.add_argument("--interval-seconds", type=float, default=settings.replay_interval_seconds)
    return parser.parse_args()


async def replay_once(
    *,
    year: int = 2025,
    min_magnitude: float = 4.0,
    event_type: str = "earthquake",
    interval_seconds: float = 0.0,
) -> list[dict]:
    run_id = uuid4()
    started_at = datetime.now(timezone.utc)
    source_label = (
        f"{USGS_CATALOG_URL}:year={year}:magnitude>={min_magnitude}:type={event_type}"
    )
    async with session_factory() as session:
        async with session.begin():
            session.add(
                IngestionRun(
                    run_id=run_id,
                    mode="replay",
                    source=source_label,
                    started_at=started_at,
                    outcome="running",
                )
            )

    try:
        events, query_metadata = await fetch_replay_events(
            year=year,
            min_magnitude=min_magnitude,
            event_type=event_type,
        )
    except Exception as exc:
        async with session_factory() as session:
            async with session.begin():
                run = await session.get(IngestionRun, run_id)
                if run is not None:
                    run.outcome = "failed"
                    run.finished_at = datetime.now(timezone.utc)
                    run.error_code = type(exc).__name__
                    run.error_summary = "USGS historical catalog request failed after retries"
        logger.error("Historical USGS request failed: %s", type(exc).__name__)
        raise

    result: list[dict] = []
    producer = await create_producer()
    try:
        for index, feature in enumerate(events):
            event_payload = {
                "id": feature.get("id"),
                "properties": feature.get("properties") or {},
                "geometry": feature.get("geometry"),
                "source": "usgs-replay",
            }
            published = await publish_event(
                producer,
                "quakes.replay",
                event_payload,
                mode="replay",
                key=str(feature.get("id") or ""),
                ingestion_run_id=run_id,
            )
            if published["status"] == "published":
                result.append(published)
            if interval_seconds > 0 and index < len(events) - 1:
                await asyncio.sleep(interval_seconds)
    finally:
        await producer.stop()

    finished_at = datetime.now(timezone.utc)
    async with session_factory() as session:
        async with session.begin():
            run = await session.get(IngestionRun, run_id)
            if run is not None:
                run.outcome = "succeeded"
                run.finished_at = finished_at
                run.request_start = datetime(year, 1, 1, tzinfo=timezone.utc)
                run.request_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
                run.http_status = 200
                run.records_received = query_metadata["records_received"]
                run.error_summary = (
                    f"months_queried={query_metadata['months_queried']}; "
                    f"published={len(result)}; event_type={event_type}; min_magnitude={min_magnitude}"
                )
    return result


async def main_async() -> None:
    args = _parse_args()
    result = await replay_once(
        year=args.year,
        min_magnitude=args.min_magnitude,
        event_type=args.event_type,
        interval_seconds=args.interval_seconds,
    )
    logger.info("Published %s replay messages", len(result))
    if not result:
        logger.warning("No replay events matched the requested filters")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
