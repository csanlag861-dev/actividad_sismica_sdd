from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

import httpx

from observatorio.logging import get_logger
from observatorio.retry import retry_async

logger = get_logger("observatorio.producer.replay_source")
USGS_CATALOG_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
PAGE_SIZE = 20_000


def _next_month(month_start: date) -> date:
    if month_start.month == 12:
        return date(month_start.year + 1, 1, 1)
    return date(month_start.year, month_start.month + 1, 1)


async def fetch_replay_events(
    *,
    year: int = 2025,
    min_magnitude: float = 4.0,
    event_type: str = "earthquake",
    url: str = USGS_CATALOG_URL,
    timeout: float = 30.0,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if year < 1900 or year > datetime.now(timezone.utc).year:
        raise ValueError(f"unsupported replay year: {year}")
    if min_magnitude < -2:
        raise ValueError("min_magnitude is outside the USGS-supported range")
    if not event_type.strip():
        raise ValueError("event_type cannot be empty")

    events: list[dict[str, Any]] = []
    query_metadata = {
        "source": url,
        "year": year,
        "min_magnitude": min_magnitude,
        "event_type": event_type,
        "months_queried": 0,
        "records_received": 0,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        month_start = date(year, 1, 1)
        year_end = date(year + 1, 1, 1)
        while month_start < year_end:
            month_end = min(_next_month(month_start), year_end)
            offset = 1
            query_metadata["months_queried"] += 1
            while True:
                params = {
                    "format": "geojson",
                    "starttime": month_start.isoformat(),
                    "endtime": month_end.isoformat(),
                    "minmagnitude": str(min_magnitude),
                    "eventtype": event_type,
                    "orderby": "time-asc",
                    "limit": PAGE_SIZE,
                    "offset": offset,
                }

                async def request_page() -> dict[str, Any]:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    result = response.json()
                    if not isinstance(result, dict) or not isinstance(result.get("features"), list):
                        raise ValueError("USGS catalog response is not a GeoJSON FeatureCollection")
                    return result

                page = await retry_async(
                    request_page,
                    destination=f"USGS replay catalog {month_start.isoformat()}",
                    max_attempts=4,
                    base_delay=1.0,
                )
                page_events = [event for event in page["features"] if isinstance(event, dict)]
                events.extend(page_events)
                query_metadata["records_received"] += len(page_events)
                if len(page_events) < PAGE_SIZE:
                    break
                offset += len(page_events)
            month_start = month_end

    events.sort(key=lambda event: int((event.get("properties") or {}).get("time", 0)))
    return events, query_metadata
