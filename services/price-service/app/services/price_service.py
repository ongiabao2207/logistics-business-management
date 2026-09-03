from datetime import date

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.crud import price_crud
from app.messaging.producer import EventPublisher, NoOpEventPublisher, RabbitMQEventPublisher
from app.models.price_model import PriceList, Service
from app.schemas.price_schema import (
    EffectiveServicePriceResponse,
    PriceListCreate,
    PriceListStatus,
    PriceListUpdate,
    ServiceCreate,
    ServiceUpdate,
)


class PriceServiceError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _not_found(entity: str) -> PriceServiceError:
    return PriceServiceError(status.HTTP_404_NOT_FOUND, f"{entity} not found")


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise PriceServiceError(status.HTTP_409_CONFLICT, "Database constraint conflict") from exc


def create_service(db: Session, payload: ServiceCreate) -> Service:
    if price_crud.find_service_by_name(db, payload.name):
        raise PriceServiceError(status.HTTP_409_CONFLICT, "Service name already exists")
    entity = price_crud.create_service(db, payload)
    _commit(db)
    db.refresh(entity)
    return entity


def list_services(db: Session, offset: int, limit: int) -> list[Service]:
    return price_crud.list_services(db, offset, limit)


def get_service(db: Session, service_id: int) -> Service:
    entity = price_crud.get_service(db, service_id)
    if entity is None:
        raise _not_found("Service")
    return entity


def update_service(db: Session, service_id: int, payload: ServiceUpdate) -> Service:
    entity = get_service(db, service_id)
    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes and price_crud.find_service_by_name(db, changes["name"], service_id):
        raise PriceServiceError(status.HTTP_409_CONFLICT, "Service name already exists")
    for field, value in changes.items():
        setattr(entity, field, value)
    _commit(db)
    db.refresh(entity)
    return entity


def deactivate_service(db: Session, service_id: int) -> None:
    entity = get_service(db, service_id)
    entity.is_active = False
    _commit(db)


def _validate_details(db: Session, payload_details) -> None:
    service_ids = [detail.service_id for detail in payload_details]
    if len(service_ids) != len(set(service_ids)):
        raise PriceServiceError(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "A service may appear only once in a price list",
        )
    for service_id in service_ids:
        service = price_crud.get_service(db, service_id)
        if service is None:
            raise _not_found(f"Service {service_id}")
        if not service.is_active:
            raise PriceServiceError(
                status.HTTP_409_CONFLICT, f"Service {service_id} is inactive"
            )


def create_price_list(db: Session, payload: PriceListCreate) -> PriceList:
    if price_crud.find_price_list_by_description(db, payload.description):
        raise PriceServiceError(
            status.HTTP_409_CONFLICT, "Price list description already exists"
        )
    _validate_details(db, payload.details)
    entity = price_crud.create_price_list(db, payload)
    _commit(db)
    return price_crud.get_price_list(db, entity.id)


def list_price_lists(db: Session, offset: int, limit: int) -> list[PriceList]:
    _synchronize_price_list_statuses(db)
    return price_crud.list_price_lists(db, offset, limit)


def get_price_list(db: Session, price_list_id: str) -> PriceList:
    _synchronize_price_list_statuses(db)
    entity = price_crud.get_price_list(db, price_list_id)
    if entity is None:
        raise _not_found("Price list")
    return entity


def update_price_list(db: Session, price_list_id: str, payload: PriceListUpdate) -> PriceList:
    entity = get_price_list(db, price_list_id)
    if entity.status not in (PriceListStatus.DRAFT, PriceListStatus.REJECTED):
        raise PriceServiceError(
            status.HTTP_409_CONFLICT,
            "Only draft or rejected price lists can be updated",
        )
    changes = payload.model_dump(exclude_unset=True)

    if "description" in changes and price_crud.find_price_list_by_description(
        db, changes["description"], entity.id
    ):
        raise PriceServiceError(
            status.HTTP_409_CONFLICT, "Price list description already exists"
        )

    start = changes.get("effective_from", entity.effective_from)
    end = changes.get("effective_to", entity.effective_to)
    if end < start:
        raise PriceServiceError(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "effective_to must be on or after effective_from",
        )

    details = payload.details if "details" in payload.model_fields_set else None
    changes.pop("details", None)
    if details is not None:
        _validate_details(db, details)
        price_crud.replace_price_details(db, entity, details)

    for field, value in changes.items():
        setattr(entity, field, value)

    if entity.status == PriceListStatus.REJECTED:
        entity.status = PriceListStatus.DRAFT.value

    _commit(db)
    return get_price_list(db, entity.id)


def delete_price_list(db: Session, price_list_id: str) -> None:
    entity = get_price_list(db, price_list_id)
    if entity.status != PriceListStatus.DRAFT:
        raise PriceServiceError(
            status.HTTP_409_CONFLICT, "Only draft price lists can be deleted"
        )
    price_crud.delete_price_list(db, entity)
    _commit(db)


def _get_event_publisher(events: EventPublisher | None = None) -> EventPublisher:
    if events is not None:
        return events
    settings = get_settings()
    if settings.rabbitmq_enabled:
        return RabbitMQEventPublisher(settings.rabbitmq_url, settings.rabbitmq_enabled)
    return NoOpEventPublisher()


def submit_price_list(db: Session, price_list_id: str, events: EventPublisher | None = None) -> PriceList:
    entity = get_price_list(db, price_list_id)
    if entity.status != PriceListStatus.DRAFT:
        raise PriceServiceError(
            status.HTTP_409_CONFLICT, "Only draft price lists can be submitted"
        )
    if not entity.details:
        raise PriceServiceError(
            status.HTTP_409_CONFLICT, "A price list must contain at least one price"
        )
    entity.status = PriceListStatus.SUBMITTED.value
    _commit(db)
    _get_event_publisher(events).publish(
        "PRICE_LIST_SUBMITTED",
        {
            "price_list_id": price_list_id,
            "recipient_role": "ROLE_DIRECTOR",
            "title": "Bảng giá mới chờ phê duyệt",
            "content": f"Bảng giá {price_list_id} đã được gửi để phê duyệt.",
            "reference_type": "PRICE_LIST",
            "reference_id": price_list_id,
        },
    )
    return get_price_list(db, entity.id)


def _ensure_no_effective_period_conflict(db: Session, entity: PriceList) -> None:
    price_crud.lock_effective_period_check(db)
    if price_crud.has_approved_date_conflict(
        db, entity.effective_from, entity.effective_to, entity.id
    ):
        raise PriceServiceError(
            status.HTTP_409_CONFLICT,
            "Price list effective period overlaps an approved price list",
        )


def _synchronize_price_list_statuses(db: Session) -> None:
    today = date.today()
    price_crud.lock_effective_period_check(db)
    changed = False

    for entity in price_crud.list_elapsed_price_lists(db, today):
        entity.status = PriceListStatus.EXPIRED.value
        changed = True

    for entity in price_crud.list_due_approved_price_lists(db, today):
        price_crud.supersede_overlapping_effective_price_lists(
            db, entity.effective_from, entity.effective_to, entity.id
        )
        entity.status = PriceListStatus.EFFECTIVE.value
        changed = True

    if changed:
        _commit(db)


def approve_price_list(db: Session, price_list_id: str, events: EventPublisher | None = None) -> PriceList:
    entity = get_price_list(db, price_list_id)
    if entity.status != PriceListStatus.SUBMITTED:
        raise PriceServiceError(
            status.HTTP_409_CONFLICT, "Only submitted price lists can be approved"
        )
    _ensure_no_effective_period_conflict(db, entity)
    today = date.today()
    if entity.effective_to < today:
        raise PriceServiceError(
            status.HTTP_409_CONFLICT, "Expired price lists cannot be approved"
        )
    if entity.effective_from > today:
        entity.status = PriceListStatus.APPROVED.value
    else:
        price_crud.supersede_overlapping_effective_price_lists(
            db, entity.effective_from, entity.effective_to, entity.id
        )
        entity.status = PriceListStatus.EFFECTIVE.value
    _commit(db)
    _get_event_publisher(events).publish(
        "PRICE_LIST_APPROVED",
        {
            "price_list_id": price_list_id,
            "recipient_role": "ROLE_SALE",
            "title": "Bảng giá đã được phê duyệt",
            "content": f"Bảng giá {price_list_id} đã được phê duyệt.",
            "reference_type": "PRICE_LIST",
            "reference_id": price_list_id,
        },
    )
    return get_price_list(db, entity.id)


def reject_price_list(db: Session, price_list_id: str, events: EventPublisher | None = None) -> PriceList:
    entity = get_price_list(db, price_list_id)
    if entity.status != PriceListStatus.SUBMITTED:
        raise PriceServiceError(
            status.HTTP_409_CONFLICT, "Only submitted price lists can be rejected"
        )
    entity.status = PriceListStatus.REJECTED.value
    _commit(db)
    _get_event_publisher(events).publish(
        "PRICE_LIST_REJECTED",
        {
            "price_list_id": price_list_id,
            "recipient_role": "ROLE_SALE",
            "title": "Bảng giá bị từ chối",
            "content": f"Bảng giá {price_list_id} đã bị từ chối.",
            "reference_type": "PRICE_LIST",
            "reference_id": price_list_id,
        },
    )
    return get_price_list(db, entity.id)


def get_effective_service_price(db: Session, service_id: int) -> EffectiveServicePriceResponse:
    _synchronize_price_list_statuses(db)
    service = get_service(db, service_id)
    result = price_crud.get_effective_service_price(db, service_id)
    if result is None:
        raise PriceServiceError(
            status.HTTP_404_NOT_FOUND, "No effective price found for this service"
        )
    price_list, detail = result
    return EffectiveServicePriceResponse(
        price_list_id=price_list.id,
        service_id=service.id,
        service_name=service.name,
        unit=service.unit,
        unit_price=detail.unit_price,
        effective_from=price_list.effective_from,
        effective_to=price_list.effective_to,
    )
