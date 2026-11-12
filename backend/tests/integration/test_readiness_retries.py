from __future__ import annotations

import pytest

from observatorio import health
from observatorio.retry import retry_async


@pytest.mark.asyncio
async def test_dependency_recovery_reaches_ready_without_restarting_service(monkeypatch) -> None:
    postgres_results = iter((False, True, True))
    kafka_results = iter((False, True))

    async def postgres(_service):
        return next(postgres_results)

    async def kafka():
        return next(kafka_results)

    monkeypatch.setattr(health, "_check_postgres", postgres)
    monkeypatch.setattr(health, "_check_kafka", kafka)

    assert not await health.check_health("productor")
    assert not await health.check_health("productor")
    assert await health.check_health("productor")


@pytest.mark.asyncio
async def test_retry_uses_progressive_delay_and_returns_after_dependency_recovers(monkeypatch) -> None:
    calls = 0
    delays: list[float] = []

    async def operation():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ConnectionError("dependency not ready")
        return "ready"

    async def sleep(delay: float):
        delays.append(delay)

    monkeypatch.setattr("observatorio.retry.asyncio.sleep", sleep)
    result = await retry_async(operation, base_delay=0.25, max_delay=1, destination="test dependency")

    assert result == "ready"
    assert calls == 3
    assert delays == [0.25, 0.5]
