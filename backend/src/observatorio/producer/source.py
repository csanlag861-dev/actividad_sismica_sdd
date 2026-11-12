from __future__ import annotations

from typing import Any

import httpx

from observatorio.config import settings
from observatorio.logging import get_logger
from observatorio.retry import retry_async

logger = get_logger("observatorio.producer.source")


async def fetch_recent_feed(url: str | None = None, timeout: float = 15.0) -> dict[str, Any]:
    feed_url = url or settings.usgs_url
    async def _request() -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(feed_url)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("USGS response payload is not a JSON object")
            return data
    return await retry_async(_request, destination=f"USGS feed {feed_url}", max_attempts=4, base_delay=1.0)


def extract_features(payload: dict[str, Any]) -> list[dict[str, Any]]:
    features = payload.get("features", [])
    return [feature for feature in features if isinstance(feature, dict)]
