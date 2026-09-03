import json
import logging
from threading import Event, Thread

import pika

from app.db.session import SessionLocal
from app.services.notification_service import NotificationService

LOGGER = logging.getLogger(__name__)
EXCHANGE = "business.events"
QUEUE = "notification.business-events"
ROUTING_KEYS = ("production.#", "contract.#", "price.#", "payment.#", "identity.#")


class NotificationConsumer:
    def __init__(self, rabbitmq_url: str) -> None:
        self.rabbitmq_url = rabbitmq_url
        self.stop_event = Event()
        self.thread = Thread(target=self._run, name="notification-consumer", daemon=True)
        self.connection = None

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.connection and self.connection.is_open:
            self.connection.add_callback_threadsafe(self.connection.close)
        self.thread.join(timeout=5)

    def _run(self) -> None:
        while not self.stop_event.is_set():
            try:
                self.connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
                channel = self.connection.channel()
                channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
                channel.queue_declare(queue=QUEUE, durable=True)
                for routing_key in ROUTING_KEYS:
                    channel.queue_bind(queue=QUEUE, exchange=EXCHANGE, routing_key=routing_key)
                channel.basic_qos(prefetch_count=10)
                channel.basic_consume(queue=QUEUE, on_message_callback=self._handle_message)
                channel.start_consuming()
            except Exception as exc:
                if not self.stop_event.is_set():
                    LOGGER.warning("Notification consumer reconnecting after error: %s", exc)
                    self.stop_event.wait(2)

    @staticmethod
    def _handle_message(channel, method, _properties, body: bytes) -> None:
        try:
            event = json.loads(body)
            payload = event.get("payload", {})
            if not payload.get("recipient_role") and not payload.get("recipient_roles"):
                channel.basic_ack(delivery_tag=method.delivery_tag)
                return
            with SessionLocal() as db:
                NotificationService(db).create_from_event(event)
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            LOGGER.exception("Could not process notification event")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
