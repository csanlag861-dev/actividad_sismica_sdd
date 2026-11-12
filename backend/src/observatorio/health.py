from __future__ import annotations

import asyncio

from aiokafka import AIOKafkaProducer
from sqlalchemy import text

from observatorio.config import settings
from observatorio.db.session import engine
from observatorio.logging import get_logger

logger = get_logger("observatorio.health")


async def _check_postgres(service_name: str) -> bool:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
        if service_name == "api":
            from observatorio.api.bootstrap import verify_revision_applied

            return await verify_revision_applied()
        if service_name == "productor":
            await conn.execute(text("SELECT 1 FROM published_version LIMIT 0"))
        elif service_name == "consumidor":
            await conn.execute(text("SELECT 1 FROM event_version LIMIT 0"))
            await conn.execute(text("SELECT 1 FROM quarantine LIMIT 0"))
    return True


async def _check_kafka() -> bool:
    producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers, request_timeout_ms=5000)
    started = False
    try:
        await asyncio.wait_for(producer.start(), timeout=10)
        started = True
    finally:
        if started:
            await producer.stop()
    return True


async def check_health(service_name: str) -> bool:
    name = (service_name or "").lower()
    if name not in {"api", "productor", "consumidor"}:
        return False
    try:
        if not await _check_postgres(name):
            return False
        if name in {"productor", "consumidor"}:
            return await _check_kafka()
        return True
    except Exception as exc:  # Healthcheck must return a failing exit status during outages.
        logger.warning("%s dependency readiness failed: %s", name, type(exc).__name__)
        return False
