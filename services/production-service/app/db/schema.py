from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.db.base import Base


def ensure_schema(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_outbox_retry_columns(engine)


def _ensure_outbox_retry_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_table("outbox_events"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("outbox_events")}
    statements = []
    if "publish_attempts" not in existing_columns:
        statements.append("ALTER TABLE outbox_events ADD COLUMN publish_attempts INTEGER NOT NULL DEFAULT 0")
    if "last_publish_error" not in existing_columns:
        statements.append("ALTER TABLE outbox_events ADD COLUMN last_publish_error TEXT")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
