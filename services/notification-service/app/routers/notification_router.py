from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.notification_schema import NotificationListResponse, NotificationResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(db)


@router.get("", response_model=NotificationListResponse)
def list_notifications(current_user: Annotated[CurrentUser, Depends(get_current_user)], service: NotificationService = Depends(get_notification_service)) -> NotificationListResponse:
    items, unread_count = service.list_for_role(current_user.role)
    return NotificationListResponse(items=items, unread_count=unread_count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(notification_id: int, current_user: Annotated[CurrentUser, Depends(get_current_user)], service: NotificationService = Depends(get_notification_service)) -> NotificationResponse:
    return service.mark_read(notification_id, current_user.role)
