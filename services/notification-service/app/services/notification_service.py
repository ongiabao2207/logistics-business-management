from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.notification_model import Notification


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_from_event(self, event: dict) -> Notification | None:
        event_id = event["event_id"]
        payload = event["payload"]
        roles = payload.get("recipient_roles")
        if not roles and payload.get("recipient_role"):
            roles = [payload["recipient_role"]]
        if not roles:
            return None

        notifications: list[Notification] = []
        is_multi_role = len(roles) > 1

        for role in roles:
            record_event_id = f"{event_id}:{role}" if is_multi_role else event_id
            existing = self.db.scalar(select(Notification).where(Notification.event_id == record_event_id))
            if existing:
                notifications.append(existing)
                continue

            reference_id = str(payload.get("reference_id") or payload.get("period_id") or "")
            notification = Notification(
                event_id=record_event_id,
                recipient_role=role,
                title=payload.get("title") or event["event_type"],
                content=payload.get("content") or "Có cập nhật nghiệp vụ mới.",
                notification_type=event["event_type"],
                reference_type=payload.get("reference_type") or "BUSINESS_EVENT",
                reference_id=reference_id,
            )
            self.db.add(notification)
            notifications.append(notification)

        self.db.commit()
        for notification in notifications:
            self.db.refresh(notification)

        return notifications[0] if notifications else None

    def create_from_production_locked(self, event: dict) -> Notification | None:
        return self.create_from_event(event)

    def list_for_role(self, role: str) -> tuple[list[Notification], int]:
        notifications = list(self.db.scalars(select(Notification).where(Notification.recipient_role == role).order_by(Notification.created_at.desc())))
        unread_count = self.db.scalar(select(func.count()).select_from(Notification).where(Notification.recipient_role == role, Notification.is_read.is_(False))) or 0
        return notifications, unread_count

    def mark_read(self, notification_id: int, role: str) -> Notification:
        notification = self.db.scalar(select(Notification).where(Notification.id == notification_id, Notification.recipient_role == role))
        if notification is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(notification)
        return notification
