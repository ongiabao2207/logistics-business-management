from typing import Any, Protocol


class EventPublisher(Protocol):
    def publish(self, event_name: str, payload: dict[str, Any]) -> None: ...


class NoOpEventPublisher:
    """Development publisher; replace with RabbitMQ without changing business logic."""

    def publish(self, event_name: str, payload: dict[str, Any]) -> None:
        return None
