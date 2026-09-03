from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.messaging import consumer
from app.services.notification_service import NotificationService


def make_service() -> NotificationService:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return NotificationService(Session(engine))


def locked_event(event_id: str = "evt-1") -> dict:
    return {"event_id": event_id, "event_type": "PRODUCTION_PERIOD_LOCKED", "payload": {"period_id": 7, "contract_id": "HD-2026-001", "recipient_role": "ROLE_ACCOUNTANT"}}


def test_creates_notification_from_locked_period_event() -> None:
    service = make_service()
    created = service.create_from_production_locked(locked_event())
    items, unread_count = service.list_for_role("ROLE_ACCOUNTANT")
    assert created.reference_id == "7"
    assert len(items) == 1
    assert unread_count == 1


def test_consuming_same_event_twice_is_idempotent() -> None:
    service = make_service()
    first = service.create_from_production_locked(locked_event())
    second = service.create_from_production_locked(locked_event())
    assert first.id == second.id


def test_mark_read_only_changes_matching_role() -> None:
    service = make_service()
    notification = service.create_from_production_locked(locked_event())
    updated = service.mark_read(notification.id, "ROLE_ACCOUNTANT")
    assert updated.is_read is True


def test_creates_notifications_for_multiple_roles() -> None:
    service = make_service()
    event = {
        "event_id": "evt-multi-1",
        "event_type": "CONTRACT_SUBMITTED",
        "payload": {
            "reference_id": "HD-001",
            "recipient_roles": ["ROLE_LEGAL", "ROLE_DIRECTOR"],
            "title": "Hợp đồng mới chờ duyệt",
        },
    }
    service.create_from_event(event)

    legal_items, _ = service.list_for_role("ROLE_LEGAL")
    director_items, _ = service.list_for_role("ROLE_DIRECTOR")

    assert len(legal_items) == 1
    assert legal_items[0].reference_id == "HD-001"
    assert len(director_items) == 1
    assert director_items[0].reference_id == "HD-001"


def test_consumer_deserializes_event_before_creating_notification(monkeypatch) -> None:
    received_events: list[dict] = []
    acknowledgements: list[int] = []

    class FakeSession:
        def __enter__(self):
            return object()

        def __exit__(self, *_args):
            return False

    class FakeNotificationService:
        def __init__(self, _db) -> None:
            pass

        def create_from_event(self, event: dict) -> None:
            received_events.append(event)

    class FakeChannel:
        def basic_ack(self, delivery_tag: int) -> None:
            acknowledgements.append(delivery_tag)

    class FakeMethod:
        delivery_tag = 12

    monkeypatch.setattr(consumer, "SessionLocal", FakeSession)
    monkeypatch.setattr(consumer, "NotificationService", FakeNotificationService)

    consumer.NotificationConsumer._handle_message(
        FakeChannel(),
        FakeMethod(),
        None,
        b'{"event_id":"evt-1","payload":{"recipient_role":"ROLE_ACCOUNTANT"}}',
    )

    assert received_events == [{"event_id": "evt-1", "payload": {"recipient_role": "ROLE_ACCOUNTANT"}}]
    assert acknowledgements == [12]
