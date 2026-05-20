"""Kafka event streaming producer."""

import json
from typing import Any, Optional

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class KafkaEventProducer:
    def __init__(self):
        self.settings = get_settings()
        self._producer = None

    async def start(self) -> None:
        try:
            from aiokafka import AIOKafkaProducer
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.settings.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode(),
            )
            await self._producer.start()
            logger.info("kafka_producer_started")
        except Exception as e:
            logger.warning("kafka_producer_unavailable", error=str(e))

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()

    async def publish(
        self,
        topic: str,
        event: dict[str, Any],
        key: Optional[str] = None,
    ) -> bool:
        if not self._producer:
            logger.debug("kafka_publish_mock", topic=topic, event_type=event.get("type"))
            return True
        try:
            await self._producer.send_and_wait(
                topic,
                value=event,
                key=key.encode() if key else None,
            )
            return True
        except Exception as e:
            logger.error("kafka_publish_failed", topic=topic, error=str(e))
            return False

    async def publish_metric(self, tenant_id: str, metric: dict) -> bool:
        return await self.publish(
            self.settings.kafka_topic_metrics,
            {"type": "metric", "tenant_id": tenant_id, **metric},
            key=tenant_id,
        )

    async def publish_incident(self, tenant_id: str, incident: dict) -> bool:
        return await self.publish(
            self.settings.kafka_topic_incidents,
            {"type": "incident", "tenant_id": tenant_id, **incident},
            key=tenant_id,
        )
