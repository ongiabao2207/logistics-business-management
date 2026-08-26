import json
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.production_model import OutboxEvent


def _json_default(value: object) -> str:
    if isinstance(value, (date, datetime, Decimal)):
        return value.isoformat() if not isinstance(value, Decimal) else str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def record_event(db: Session, event_type: str, aggregate_id: int, payload: dict) -> None:
    db.add(OutboxEvent(event_type=event_type, aggregate_id=str(aggregate_id), payload=json.dumps(payload, default=_json_default)))
