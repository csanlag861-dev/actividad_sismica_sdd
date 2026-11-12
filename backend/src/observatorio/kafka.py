from __future__ import annotations

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from observatorio.config import settings


def build_producer_config() -> dict:
    return {
        "bootstrap_servers": settings.kafka_bootstrap_servers,
        "acks": "all",
        "enable_idempotence": True,
        "linger_ms": 10,
    }


def build_consumer_config(group_id: str) -> dict:
    return {
        "bootstrap_servers": settings.kafka_bootstrap_servers,
        "group_id": group_id,
        "auto_offset_reset": "earliest",
        "enable_auto_commit": False,
    }


async def create_producer() -> AIOKafkaProducer:
    producer = AIOKafkaProducer(**build_producer_config())
    await producer.start()
    return producer


async def create_consumer(group_id: str, *topics: str) -> AIOKafkaConsumer:
    consumer = AIOKafkaConsumer(*topics, **build_consumer_config(group_id))
    await consumer.start()
    return consumer
