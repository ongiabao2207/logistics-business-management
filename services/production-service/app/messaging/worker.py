import logging
from threading import Event, Thread

from app.messaging.outbox_publisher import OutboxPublisher

LOGGER = logging.getLogger(__name__)


class OutboxWorker:
    def __init__(self, publisher: OutboxPublisher, poll_interval_seconds: float) -> None:
        self.publisher = publisher
        self.poll_interval_seconds = poll_interval_seconds
        self.stop_event = Event()
        self.thread = Thread(target=self._run, name="production-outbox", daemon=True)

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.thread.join(timeout=self.poll_interval_seconds + 2)

    def _run(self) -> None:
        while not self.stop_event.is_set():
            try:
                self.publisher.publish_pending()
            except Exception:
                LOGGER.exception("Unhandled Production outbox worker error")
            self.stop_event.wait(self.poll_interval_seconds)
