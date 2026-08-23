from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.price_model import PriceList, PriceListDetail, Service
from app.schemas.price_schema import PriceListCreate, PriceListDetailCreate, ServiceCreate


def create_service(db: Session, payload: ServiceCreate) -> Service:
    entity = Service(**payload.model_dump())
    db.add(entity)
    db.flush()
    db.refresh(entity)
    return entity


def list_services(db: Session, offset: int, limit: int) -> list[Service]:
    return list(db.scalars(select(Service).order_by(Service.id).offset(offset).limit(limit)))


def get_service(db: Session, service_id: int) -> Service | None:
    return db.get(Service, service_id)


def find_service_by_name(db: Session, name: str, exclude_id: int | None = None) -> Service | None:
    statement = select(Service).where(Service.name == name)
    if exclude_id is not None:
        statement = statement.where(Service.id != exclude_id)
    return db.scalar(statement)


def create_price_list(db: Session, payload: PriceListCreate) -> PriceList:
    entity = PriceList(
        description=payload.description,
        version=payload.version,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        status="DRAFT",
        details=[PriceListDetail(**detail.model_dump()) for detail in payload.details],
    )
    db.add(entity)
    db.flush()
    db.refresh(entity)
    return entity


def list_price_lists(db: Session, offset: int, limit: int) -> list[PriceList]:
    statement = (
        select(PriceList)
        .options(selectinload(PriceList.details))
        .order_by(PriceList.version.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement))


def get_price_list(db: Session, price_list_id: str) -> PriceList | None:
    statement = (
        select(PriceList)
        .options(selectinload(PriceList.details))
        .where(PriceList.id == price_list_id)
    )
    return db.scalar(statement)


def find_price_list_by_version(
    db: Session, version: int, exclude_id: str | None = None
) -> PriceList | None:
    statement = select(PriceList).where(PriceList.version == version)
    if exclude_id is not None:
        statement = statement.where(PriceList.id != exclude_id)
    return db.scalar(statement)


def replace_price_details(
    db: Session, price_list: PriceList, details: list[PriceListDetailCreate]
) -> None:
    price_list.details.clear()
    price_list.details.extend(PriceListDetail(**detail.model_dump()) for detail in details)
    db.flush()


def get_active_price_list(db: Session) -> PriceList | None:
    statement = (
        select(PriceList)
        .options(selectinload(PriceList.details))
        .where(PriceList.status == "ACTIVE")
    )
    return db.scalar(statement)


def get_active_service_price(db: Session, service_id: int) -> tuple[PriceList, PriceListDetail] | None:
    statement = (
        select(PriceListDetail)
        .join(PriceList)
        .options(selectinload(PriceListDetail.price_list))
        .where(PriceList.status == "ACTIVE", PriceListDetail.service_id == service_id)
    )
    detail = db.scalar(statement)
    if detail is None:
        return None
    return detail.price_list, detail


def delete_price_list(db: Session, price_list: PriceList) -> None:
    db.delete(price_list)
    db.flush()


def expire_active_price_list(db: Session, except_id: str) -> None:
    active = db.scalar(
        select(PriceList).where(PriceList.status == "ACTIVE", PriceList.id != except_id)
    )
    if active is not None:
        active.status = "EXPIRED"


def has_active_date_conflict(db: Session, start: date, end: date, exclude_id: str) -> bool:
    statement = select(PriceList.id).where(
        PriceList.status == "ACTIVE",
        PriceList.id != exclude_id,
        PriceList.effective_from <= end,
        PriceList.effective_to >= start,
    )
    return db.scalar(statement) is not None
