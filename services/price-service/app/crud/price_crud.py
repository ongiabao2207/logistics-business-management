from datetime import date, datetime, timezone

from sqlalchemy import func, select, text
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
        id=next_price_list_id(db),
        description=payload.description,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        status="DRAFT",
        details=[PriceListDetail(**detail.model_dump()) for detail in payload.details],
    )
    db.add(entity)
    db.flush()
    db.refresh(entity)
    return entity


def next_price_list_id(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"BG-{year}-"

    if db.get_bind().dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": f"price-list-id-{year}"},
        )

    existing_ids = db.scalars(select(PriceList.id).where(PriceList.id.like(f"{prefix}%")))
    sequences = []
    for price_list_id in existing_ids:
        suffix = price_list_id.removeprefix(prefix)
        if suffix.isdigit():
            sequences.append(int(suffix))

    return f"{prefix}{max(sequences, default=0) + 1:03d}"


def list_price_lists(db: Session, offset: int, limit: int) -> list[PriceList]:
    statement = (
        select(PriceList)
        .options(selectinload(PriceList.details))
        .order_by(PriceList.created_at.desc(), PriceList.id.desc())
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


def find_price_list_by_description(
    db: Session, description: str, exclude_id: str | None = None
) -> PriceList | None:
    statement = select(PriceList).where(
        func.lower(func.trim(PriceList.description)) == description.strip().lower()
    )
    if exclude_id is not None:
        statement = statement.where(PriceList.id != exclude_id)
    return db.scalar(statement)


def replace_price_details(
    db: Session, price_list: PriceList, details: list[PriceListDetailCreate]
) -> None:
    price_list.details.clear()
    price_list.details.extend(PriceListDetail(**detail.model_dump()) for detail in details)
    db.flush()


def get_effective_price_list(db: Session) -> PriceList | None:
    statement = (
        select(PriceList)
        .options(selectinload(PriceList.details))
        .where(PriceList.status == "EFFECTIVE")
    )
    return db.scalar(statement)


def get_effective_service_price(
    db: Session, service_id: int
) -> tuple[PriceList, PriceListDetail] | None:
    today = date.today()
    statement = (
        select(PriceListDetail)
        .join(PriceList)
        .options(selectinload(PriceListDetail.price_list))
        .where(
            PriceList.status == "EFFECTIVE",
            PriceList.effective_from <= today,
            PriceList.effective_to >= today,
            PriceListDetail.service_id == service_id,
        )
    )
    detail = db.scalar(statement)
    if detail is None:
        return None
    return detail.price_list, detail


def delete_price_list(db: Session, price_list: PriceList) -> None:
    db.delete(price_list)
    db.flush()


def supersede_overlapping_effective_price_lists(
    db: Session, start: date, end: date, except_id: str
) -> None:
    statement = select(PriceList).where(
        PriceList.status == "EFFECTIVE",
        PriceList.id != except_id,
        PriceList.effective_from <= end,
        PriceList.effective_to >= start,
    )
    for price_list in db.scalars(statement):
        price_list.status = "SUPERSEDED"


def lock_effective_period_check(db: Session) -> None:
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(hashtext('price-list-effective-period'))"))


def list_elapsed_price_lists(db: Session, today: date) -> list[PriceList]:
    statement = select(PriceList).where(
        PriceList.status.in_(("APPROVED", "EFFECTIVE")),
        PriceList.effective_to < today,
    )
    return list(db.scalars(statement))


def list_due_approved_price_lists(db: Session, today: date) -> list[PriceList]:
    statement = (
        select(PriceList)
        .where(
            PriceList.status == "APPROVED",
            PriceList.effective_from <= today,
            PriceList.effective_to >= today,
        )
        .order_by(PriceList.effective_from, PriceList.id)
    )
    return list(db.scalars(statement))


def has_approved_date_conflict(db: Session, start: date, end: date, exclude_id: str) -> bool:
    statement = select(PriceList.id).where(
        PriceList.status == "APPROVED",
        PriceList.id != exclude_id,
        PriceList.effective_from <= end,
        PriceList.effective_to >= start,
    )
    return db.scalar(statement) is not None
