from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.production_model import ProductionDetail, ProductionPeriod


def find_overlapping_periods(db: Session, customer_id: str, contract_id: str, from_date: date, to_date: date) -> list[ProductionPeriod]:
    statement = select(ProductionPeriod).where(
        ProductionPeriod.customer_id == customer_id,
        ProductionPeriod.contract_id == contract_id,
        ProductionPeriod.from_date <= to_date,
        ProductionPeriod.to_date >= from_date,
    )
    return list(db.scalars(statement))


def get_period(db: Session, period_id: int) -> ProductionPeriod | None:
    statement = select(ProductionPeriod).options(selectinload(ProductionPeriod.details)).where(ProductionPeriod.id == period_id)
    return db.scalar(statement)


def list_periods(db: Session, customer_id: str | None = None, contract_id: str | None = None) -> list[ProductionPeriod]:
    statement = select(ProductionPeriod).options(selectinload(ProductionPeriod.details)).order_by(ProductionPeriod.from_date.desc())
    if customer_id:
        statement = statement.where(ProductionPeriod.customer_id == customer_id)
    if contract_id:
        statement = statement.where(ProductionPeriod.contract_id == contract_id)
    return list(db.scalars(statement))


def create_period(db: Session, period: ProductionPeriod) -> ProductionPeriod:
    db.add(period)
    db.flush()
    return period


def replace_details(period: ProductionPeriod, details: list[ProductionDetail]) -> None:
    period.details.clear()
    period.details.extend(details)
