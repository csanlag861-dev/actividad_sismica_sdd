from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

from observatorio.logging import get_logger
from observatorio.producer.source import safe_source_url

logger = get_logger("observatorio.producer.replay_source")
USGS_CATALOG_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
PAGE_SIZE = 20_000
MIN_SPLIT_INTERVAL = timedelta(milliseconds=2)
RETRY_DELAYS = (1.0, 2.0, 4.0)


@dataclass(frozen=True)
class ReplayResponse:
    interval_start: datetime
    interval_end: datetime
    params: dict[str, str]
    url: str
    status_code: int
    content: bytes
    payload: dict[str, Any]
    requested_at: datetime
    received_at: datetime
    attempts: int

    @property
    def features(self) -> list[dict[str, Any]]:
        return self.payload["features"]

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _format_timestamp(value: datetime) -> str:
    normalized = _as_utc(value)
    if normalized.time() == datetime.min.time():
        return normalized.date().isoformat()
    return normalized.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def split_interval(start: datetime, end: datetime) -> tuple[datetime, datetime]:
    start_utc, end_utc = _as_utc(start), _as_utc(end)
    if end_utc - start_utc < MIN_SPLIT_INTERVAL:
        raise ValueError("USGS response reached the limit in an interval that cannot be split safely")
    duration_ms = int((end_utc - start_utc).total_seconds() * 1000)
    midpoint = start_utc + timedelta(milliseconds=duration_ms // 2)
    if midpoint <= start_utc or midpoint >= end_utc:
        raise ValueError("USGS response reached the limit in an interval that cannot be split safely")
    return midpoint, midpoint


def _validate_query(
    *,
    year: int,
    min_magnitude: float,
    event_type: str,
    start: datetime | None,
    end: datetime | None,
) -> tuple[datetime, datetime]:
    if (start is None) != (end is None):
        raise ValueError("both start and end UTC timestamps must be provided")
    if start is None:
        if year < 1900 or year > datetime.now(timezone.utc).year:
            raise ValueError(f"unsupported replay year: {year}")
        return datetime(year, 1, 1, tzinfo=timezone.utc), datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    start_utc, end_utc = _as_utc(start), _as_utc(end)
    if end_utc <= start_utc:
        raise ValueError("replay end must be later than replay start")
    return start_utc, end_utc


def _month_intervals(start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
    intervals: list[tuple[datetime, datetime]] = []
    current = start
    while current < end:
        if current.day == 1 and current.time() == datetime.min.time():
            next_month = (
                datetime(current.year + 1, 1, 1, tzinfo=timezone.utc)
                if current.month == 12
                else datetime(current.year, current.month + 1, 1, tzinfo=timezone.utc)
            )
        else:
            next_month = current + timedelta(days=31)
            next_month = datetime(next_month.year, next_month.month, 1, tzinfo=timezone.utc)
            if next_month <= current:
                next_month = datetime(current.year + 1, 1, 1, tzinfo=timezone.utc)
        interval_end = min(next_month, end)
        intervals.append((current, interval_end))
        current = interval_end
    return intervals


async def fetch_interval_response(
    client: httpx.AsyncClient,
    *,
    interval_start: datetime,
    interval_end: datetime,
    min_magnitude: float = 4.0,
    event_type: str = "earthquake",
    url: str = USGS_CATALOG_URL,
    timeout: float = 30.0,
) -> ReplayResponse:
    def reject_constant(value: str) -> None:
        raise ValueError(f"USGS response contains non-standard JSON number {value}")

    params = {
        "format": "geojson",
        "starttime": _format_timestamp(interval_start),
        "endtime": _format_timestamp(interval_end),
        "minmagnitude": str(min_magnitude),
        "eventtype": event_type,
        "orderby": "time-asc",
        "limit": str(PAGE_SIZE),
    }

    async def request() -> ReplayResponse:
        requested_at = datetime.now(timezone.utc)
        response = await client.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        try:
            payload = json.loads(response.content, parse_constant=reject_constant)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("USGS catalog response is not valid JSON") from exc
        if (
            not isinstance(payload, dict)
            or payload.get("type") != "FeatureCollection"
            or not isinstance(payload.get("features"), list)
            or any(not isinstance(feature, dict) for feature in payload["features"])
        ):
            raise ValueError("USGS catalog response is not a GeoJSON FeatureCollection")
        return ReplayResponse(
            interval_start=_as_utc(interval_start),
            interval_end=_as_utc(interval_end),
            params=params,
            url=str(response.url),
            status_code=response.status_code,
            content=response.content,
            payload=payload,
            requested_at=requested_at,
            received_at=datetime.now(timezone.utc),
            attempts=1,
        )

    delay_index = 0
    attempts = 0
    while True:
        attempts += 1
        try:
            result = await request()
            return ReplayResponse(
                interval_start=result.interval_start,
                interval_end=result.interval_end,
                params=result.params,
                url=result.url,
                status_code=result.status_code,
                content=result.content,
                payload=result.payload,
                requested_at=result.requested_at,
                received_at=result.received_at,
                attempts=attempts,
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 429 and exc.response.status_code < 500:
                raise
            last_error: Exception = exc
        except (httpx.TransportError, ValueError) as exc:
            last_error = exc

        if delay_index >= len(RETRY_DELAYS):
            logger.error("Historical USGS interval failed after retries: %s", type(last_error).__name__)
            raise last_error
        await asyncio.sleep(RETRY_DELAYS[delay_index])
        delay_index += 1


def _feature_identity(feature: dict[str, Any]) -> tuple[str | None, str | None]:
    properties = feature.get("properties") or {}
    return (
        str(feature["id"]) if feature.get("id") is not None else None,
        str(properties["updated"]) if properties.get("updated") is not None else None,
    )


async def fetch_replay_events(
    *,
    year: int = 2025,
    min_magnitude: float = 4.0,
    event_type: str = "earthquake",
    url: str = USGS_CATALOG_URL,
    timeout: float = 30.0,
    start: datetime | None = None,
    end: datetime | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
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
    metadata: dict[str, Any] = {
        "source": safe_source_url(url),
        "year": year if start is None else None,
        "start": range_start.isoformat(),
        "end": range_end.isoformat(),
        "min_magnitude": min_magnitude,
        "event_type": event_type,
        "months_queried": len(intervals),
        "queries_issued": 0,
        "records_received": 0,
        "unique_versions": 0,
    }
    unique_features: dict[tuple[str | None, str | None], dict[str, Any]] = {}

    async with httpx.AsyncClient(timeout=timeout) as client:
        async def collect_interval(interval_start: datetime, interval_end: datetime) -> None:
            response = await fetch_interval_response(
                client,
                interval_start=interval_start,
                interval_end=interval_end,
                min_magnitude=min_magnitude,
                event_type=event_type,
                url=url,
                timeout=timeout,
            )
            metadata["queries_issued"] += 1
            metadata["records_received"] += len(response.features)
            if len(response.features) >= PAGE_SIZE:
                midpoint, right_start = split_interval(interval_start, interval_end)
                await collect_interval(interval_start, midpoint)
                await collect_interval(right_start, interval_end)
                return
            for feature in response.features:
                identity = _feature_identity(feature)
                if identity == (None, None):
                    identity = (None, f"unidentified-{len(unique_features)}")
                unique_features[identity] = feature

        for interval_start, interval_end in intervals:
            await collect_interval(interval_start, interval_end)

    events = list(unique_features.values())
    events.sort(key=lambda event: int((event.get("properties") or {}).get("time", 0)))
    metadata["unique_versions"] = len(events)
    return events, metadata
