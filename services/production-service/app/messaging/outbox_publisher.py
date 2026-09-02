"""Reliable bridge from Production's transactional outbox to RabbitMQ."""

import json
import logging
from datetime import datetime, timezone

import pika
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.production_model import OutboxEvent

LOGGER = logging.getLogger(__name__)
EXCHANGE = "business.events"


class OutboxPublisher:
    def __init__(self, rabbitmq_url: str) -> None:
        self.rabbitmq_url = rabbitmq_url

    def publish_pending(self) -> int:
        """Publish unpublished events and mark them sent only after broker confirmation."""
        with SessionLocal() as db:
            events = list(db.scalars(select(OutboxEvent).where(OutboxEvent.published_at.is_(None)).order_by(OutboxEvent.id).limit(100)))
            if not events:
                return 0
            try:
                connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
                channel = connection.channel()
                channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
                for event in events:
                    routing_key = "production.period." + event.event_type.removeprefix("PRODUCTION_PERIOD_").lower().replace("_", "-")
                    envelope = {
                        "event_id": str(event.id),
                        "event_type": event.event_type,
                        "aggregate_id": event.aggregate_id,
                        "occurred_at": event.created_at.isoformat(),
                        "payload": json.loads(event.payload),
                    }
                    channel.basic_publish(
                        exchange=EXCHANGE,
                        routing_key=routing_key,
                        body=json.dumps(envelope),
                        properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
                    )
                    event.publish_attempts += 1
                    event.published_at = datetime.now(timezone.utc)
                    event.last_publish_error = None
                connection.close()
                db.commit()
                return len(events)
            except Exception as exc:
                for event in events:
                    event.publish_attempts += 1
                    event.last_publish_error = str(exc)[:1000]
                db.commit()
                LOGGER.warning("Could not publish Production outbox events: %s", exc)
                return 0
