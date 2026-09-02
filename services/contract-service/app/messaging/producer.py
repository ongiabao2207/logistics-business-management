import json
import logging
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

import pika

LOGGER = logging.getLogger(__name__)
EXCHANGE = "business.events"


class EventPublisher(Protocol):
    def publish(self, event_name: str, payload: dict[str, Any]) -> None: ...


class NoOpEventPublisher:
    """Development publisher; replace with RabbitMQ without changing business logic."""

    def publish(self, event_name: str, payload: dict[str, Any]) -> None:
        return None


class RabbitMQEventPublisher:
    """Best-effort notification event publisher; never changes contract outcomes."""

    def __init__(self, rabbitmq_url: str, enabled: bool) -> None:
        self.rabbitmq_url = rabbitmq_url
        self.enabled = enabled

    def publish(self, event_name: str, payload: dict[str, Any]) -> None:
        if not self.enabled:
            return
        try:
            connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            channel = connection.channel()
            channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
            channel.basic_publish(
                exchange=EXCHANGE,
                routing_key=f"contract.{event_name.lower()}",
                body=json.dumps({
                    "event_id": str(uuid4()),
                    "event_type": event_name,
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                    "payload": payload,
                }),
                properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
            )
            connection.close()
        except Exception:
            LOGGER.exception("Could not publish contract event %s", event_name)
