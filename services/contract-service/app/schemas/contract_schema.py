from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ContractCreate(BaseModel):
    customer_id: str = Field(..., min_length=1, max_length=36)
    valid_from: date
    valid_to: date
    payment_terms: str = Field(..., min_length=1, max_length=255)
    service_ids: list[int] = Field(..., min_length=1)


class ContractServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    service_name: str
    service_unit: str
    service_price: Decimal


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
