from fastapi import status
from sqlalchemy.orm import Session

from app.crud import customer_crud
from app.schemas.customer_schema import CustomerResponse


class CustomerServiceError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class CustomerService:
    def list_customers(
        self, db: Session, offset: int, limit: int
    ) -> list[CustomerResponse]:
        return [
            CustomerResponse.model_validate(customer)
            for customer in customer_crud.list_customers(db, offset, limit)
        ]

    def get_customer(self, db: Session, customer_id: str) -> CustomerResponse:
        customer = customer_crud.get_customer(db, customer_id)
        if customer is None:
            raise CustomerServiceError(
                status.HTTP_404_NOT_FOUND,
                "customer does not exist",
            )

        return CustomerResponse.model_validate(customer)
