from __future__ import annotations

import asyncio

from aiokafka import AIOKafkaConsumer, TopicPartition
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from observatorio.db.session import session_factory
from observatorio.consumer.processor import persist_message
from observatorio.kafka import create_consumer
from observatorio.logging import get_logger

logger = get_logger("observatorio.consumer.main")
KAFKA_TOPICS = ("quakes.live", "quakes.replay")


async def handle_message(
    consumer: AIOKafkaConsumer,
    message: object,
    *,
    database_sessions: async_sessionmaker[AsyncSession] = session_factory,
) -> str:
    raw_message = getattr(message, "value", None) or b""
    topic = getattr(message, "topic")
    partition = getattr(message, "partition")
    offset = getattr(message, "offset")
    outcome = await persist_message(
        database_sessions,
        raw_message,
        topic=topic,
        partition=partition,
        offset=offset,
    )
    tp = TopicPartition(topic, partition)
    await consumer.commit({tp: offset + 1})
    logger.info("Persisted Kafka message %s/%s@%s with outcome=%s", topic, partition, offset, outcome)
    return outcome


async def consume_once(
    *,
    topics: tuple[str, ...] = KAFKA_TOPICS,
    group_id: str = "observatorio-consumer",
    database_sessions: async_sessionmaker[AsyncSession] = session_factory,
) -> None:
    consumer: AIOKafkaConsumer = await create_consumer(group_id, *topics)
    try:
        logger.info("Consumer subscribed to %s", ",".join(topics))
        async for message in consumer:
            await handle_message(consumer, message, database_sessions=database_sessions)
    finally:
        await consumer.stop()


async def run_consumer() -> None:
    delay = 1.0
    while True:
        try:
            await consume_once()
            delay = 1.0
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - runtime guard
            logger.warning("Consumer connection or processing failed; retrying in %.1fs: %s", delay, type(exc).__name__)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30.0)


def main() -> None:
    asyncio.run(run_consumer())


if __name__ == "__main__":
    main()
