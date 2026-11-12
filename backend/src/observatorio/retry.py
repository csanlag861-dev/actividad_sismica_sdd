from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from observatorio.logging import get_logger

logger = get_logger("observatorio.retry")


async def retry_async(
    operation: Callable[[], Awaitable[Any]],
    *,
    max_attempts: int = 5,
    base_delay: float = 0.5,
    max_delay: float = 10.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    destination: str = "service",
) -> Any:
    delay = base_delay
    for attempt in range(1, max_attempts + 1):
        try:
            return await operation()
        except exceptions as exc:
            if attempt == max_attempts:
                logger.error("Retry exhausted for %s after %s attempts: %s", destination, attempt, exc)
                raise
            logger.warning(
                "Retrying %s in %.2fs (attempt %s/%s): %s",
                destination,
                delay,
                attempt,
                max_attempts,
                exc,
            )
            await asyncio.sleep(delay)
            delay = min(delay * 2, max_delay)
    raise RuntimeError(f"retry_async for {destination} did not complete")
