from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, require_roles
from app.db.session import get_db
from app.schemas.customer_schema import CustomerResponse
from app.services.customer_service import CustomerService


router = APIRouter(prefix="/api/v1")


def get_customer_service() -> CustomerService:
    return CustomerService()


@router.get("/customers", response_model=list[CustomerResponse])
def list_customers(
    _user: Annotated[
        CurrentUser,
        Depends(require_roles("ROLE_SALE", "ROLE_ACCOUNTANT", "ROLE_LEGAL", "ROLE_DIRECTOR")),
    ],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    service: CustomerService = Depends(get_customer_service),
):
    return service.list_customers(db, offset, limit)


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: str,
    _user: Annotated[
        CurrentUser,
        Depends(require_roles("ROLE_SALE", "ROLE_ACCOUNTANT", "ROLE_LEGAL", "ROLE_DIRECTOR")),
    ],
    db: Session = Depends(get_db),
    service: CustomerService = Depends(get_customer_service),
):
    return service.get_customer(db, customer_id)
