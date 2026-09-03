from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer_model import CustomerInfo


def list_customers(db: Session, offset: int, limit: int) -> list[CustomerInfo]:
    statement = (
        select(CustomerInfo)
        .order_by(CustomerInfo.id)
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


def get_customer(db: Session, customer_id: str) -> CustomerInfo | None:
    return db.get(CustomerInfo, customer_id)
