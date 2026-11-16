from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

from observatorio.config import settings
from observatorio.logging import get_logger

logger = get_logger("observatorio.producer.source")
RETRY_DELAYS = (1.0, 2.0, 4.0)


@dataclass(frozen=True)
class FeedResponse:
    url: str
    status_code: int
    content: bytes
    payload: dict[str, Any]
    requested_at: datetime
    received_at: datetime
    attempts: int


def safe_source_url(url: str) -> str:
    parsed = urlsplit(url)
    safe_query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not any(term in key.casefold() for term in ("token", "secret", "password", "key", "auth"))
    ]
    hostname = parsed.hostname or ""
    if parsed.port is not None:
        hostname = f"{hostname}:{parsed.port}"
    return urlunsplit((parsed.scheme, hostname, parsed.path, urlencode(safe_query), ""))


def _decode_feed(content: bytes) -> dict[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"USGS response contains non-standard JSON number {value}")

    try:
        data = json.loads(content, parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("USGS response is not valid JSON") from exc
    if (
        not isinstance(data, dict)
        or data.get("type") != "FeatureCollection"
        or not isinstance(data.get("features"), list)
    ):
        raise ValueError("USGS response is not a GeoJSON FeatureCollection")
    if any(not isinstance(feature, dict) for feature in data["features"]):
        raise ValueError("USGS FeatureCollection contains a non-object feature")
    return data


async def fetch_recent_response(
    url: str | None = None,
    timeout: float | None = None,
) -> FeedResponse:
    feed_url = url or settings.usgs_url
    request_timeout = settings.usgs_timeout_seconds if timeout is None else timeout
    last_error: Exception | None = None

    async with httpx.AsyncClient(timeout=request_timeout) as client:
        for attempt in range(1, len(RETRY_DELAYS) + 2):
            requested_at = datetime.now(timezone.utc)
            try:
                response = await client.get(feed_url)
                response.raise_for_status()
                data = _decode_feed(response.content)
                return FeedResponse(
                    url=str(response.url),
                    status_code=response.status_code,
                    content=response.content,
                    payload=data,
                    requested_at=requested_at,
                    received_at=datetime.now(timezone.utc),
                    attempts=attempt,
                )
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                retryable = status_code == 429 or status_code >= 500
                last_error = exc
                if not retryable:
                    raise
            except (httpx.TransportError, ValueError) as exc:
                last_error = exc

            if attempt > len(RETRY_DELAYS):
                assert last_error is not None
                logger.error(
                    "USGS request failed after %s attempts: %s",
                    attempt,
                    type(last_error).__name__,
                )
                raise last_error
            await asyncio.sleep(RETRY_DELAYS[attempt - 1])

    raise RuntimeError("USGS retry loop exited without a result")


async def fetch_recent_feed(url: str | None = None, timeout: float | None = None) -> dict[str, Any]:
    return (await fetch_recent_response(url, timeout)).payload


def extract_features(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("type") != "FeatureCollection" or not isinstance(payload.get("features"), list):
        raise ValueError("USGS response is not a GeoJSON FeatureCollection")
    features = payload["features"]
    if any(not isinstance(feature, dict) for feature in features):
        raise ValueError("USGS FeatureCollection contains a non-object feature")
    return features
