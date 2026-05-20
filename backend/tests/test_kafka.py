"""Kafka event streaming validation tests."""

from __future__ import annotations

import asyncio
import json
import os
import uuid

import pytest

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TEST_TOPIC = os.getenv("KAFKA_TEST_TOPIC", "sentinel.metrics")


def _kafka_available() -> bool:
    try:
        from kafka import KafkaAdminClient
        admin = KafkaAdminClient(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            request_timeout_ms=8000,
            api_version_auto_timeout_ms=8000,
        )
        admin.describe_cluster()
        admin.close()
        return True
    except Exception:
        return False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_kafka_producer_start_stop():
    from app.services.kafka_producer import KafkaEventProducer

    producer = KafkaEventProducer()
    await producer.start()
    # Should not raise even if Kafka unavailable (graceful fallback)
    await producer.stop()


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not _kafka_available(), reason="Kafka not available")
async def test_kafka_publish_metric():
    from app.services.kafka_producer import KafkaEventProducer
    from app.config import get_settings

    settings = get_settings()
    producer = KafkaEventProducer()
    await producer.start()

    event = {"metric_name": "test.latency", "value": 42.0, "service": "test-service"}
    success = await producer.publish_metric("default", event)
    assert success is True

    await producer.stop()


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not _kafka_available(), reason="Kafka not available")
async def test_kafka_event_serialization():
    from app.services.kafka_producer import KafkaEventProducer

    producer = KafkaEventProducer()
    await producer.start()

    payload = {
        "type": "metric",
        "tenant_id": "test",
        "metric_name": "cpu.usage",
        "value": 91.5,
    }
    # Verify JSON serializable
    serialized = json.dumps(payload)
    assert "cpu.usage" in serialized

    success = await producer.publish("sentinel.metrics", payload, key="test")
    assert success is True
    await producer.stop()


@pytest.mark.integration
@pytest.mark.skipif(not _kafka_available(), reason="Kafka not available")
def test_kafka_broker_connection():
    from kafka import KafkaAdminClient

    admin = KafkaAdminClient(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        request_timeout_ms=10000,
    )
    cluster = admin.describe_cluster()
    admin.close()
    assert len(cluster.get("brokers", [])) >= 1


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not _kafka_available(), reason="Kafka not available")
async def test_kafka_consume_published_event():
    """Publish via aiokafka and consume back to validate round-trip."""
    from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

    test_key = f"test-{uuid.uuid4().hex[:8]}"
    test_value = {"test_id": test_key, "source": "test_kafka.py"}

    async def _round_trip():
        producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode(),
        )
        await producer.start()
        await producer.send_and_wait(TEST_TOPIC, value=test_value, key=test_key.encode())
        await producer.stop()

        consumer = AIOKafkaConsumer(
            TEST_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            auto_offset_reset="latest",
            group_id=f"test-group-{test_key}",
            value_deserializer=lambda m: json.loads(m.decode()),
            consumer_timeout_ms=15000,
        )
        await consumer.start()
        try:
            async for msg in consumer:
                if msg.value.get("test_id") == test_key:
                    return msg.value
        finally:
            await consumer.stop()
        return None

    result = await asyncio.wait_for(_round_trip(), timeout=30)
    assert result is not None
    assert result["test_id"] == test_key


@pytest.mark.integration
@pytest.mark.asyncio
async def test_kafka_producer_retry_on_unavailable():
    """Producer should gracefully degrade when Kafka is unreachable."""
    from app.services.kafka_producer import KafkaEventProducer

    producer = KafkaEventProducer()
    # Force unavailable bootstrap
    producer.settings.kafka_bootstrap_servers = "localhost:59999"
    await producer.start()
    # publish should mock/log, not crash
    result = await producer.publish("sentinel.metrics", {"type": "test"})
    assert result is True
    await producer.stop()
