from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ContractServiceCreate(BaseModel):
    service_id: int
    quantity: int = Field(..., gt=0)


class ContractCreate(BaseModel):
    customer_id: str = Field(..., min_length=1, max_length=36)
    valid_from: date
    valid_to: date
    payment_terms: str = Field(..., min_length=1, max_length=255)
    services: list[ContractServiceCreate] = Field(..., min_length=1)


class ContractStatusUpdate(BaseModel):
    status: Literal["DRAFT", "SUBMITTED", "APPROVED", "REJECTED", "ACTIVE", "EXPIRED"]


class ContractReview(BaseModel):
    decision: Literal["APPROVE", "REJECT"]


class ContractUpdate(BaseModel):
    valid_from: date | None = None
    valid_to: date | None = None
    payment_terms: str | None = Field(default=None, min_length=1, max_length=255)
    services: list[ContractServiceCreate] | None = Field(default=None, min_length=1)


class ContractServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    service_name: str
    service_unit: str
    service_price: Decimal
    quantity: int


class ContractSummaryRead(BaseModel):
    contract_id: str
    customer_name: str
    valid_from: date
    valid_to: date
    total_value: Decimal
    status: str


class ContractDetailServiceRead(BaseModel):
    id: int
    service_name: str
    service_unit: str
    service_price: Decimal
    quantity: int


class ContractDetailRead(ContractSummaryRead):
    payment_terms: str
    updated_at: datetime
    services: list[ContractDetailServiceRead]


class ContractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    valid_from: date
    valid_to: date
    payment_terms: str
    status: str
    created_at: datetime
    updated_at: datetime
    services: list[ContractServiceRead]
