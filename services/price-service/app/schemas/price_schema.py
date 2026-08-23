from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PriceListStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=500)
    is_active: bool = True
    unit: str = Field(min_length=1, max_length=50)


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    is_active: bool | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=50)


class ServiceResponse(BaseModel):
    id: int
    name: str
    description: str
    is_active: bool
    unit: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PriceListDetailCreate(BaseModel):
    service_id: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0, max_digits=18, decimal_places=2)


class PriceListDetailResponse(BaseModel):
    id: int
    service_id: int
    unit_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class PriceListDatesMixin(BaseModel):
    effective_from: date
    effective_to: date

    @model_validator(mode="after")
    def validate_effective_period(self):
        if self.effective_to < self.effective_from:
            raise ValueError("effective_to must be on or after effective_from")
        return self


class PriceListCreate(PriceListDatesMixin):
    description: str = Field(min_length=1, max_length=500)
    version: int = Field(gt=0)
    details: list[PriceListDetailCreate] = Field(min_length=1)


class PriceListUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=500)
    version: int | None = Field(default=None, gt=0)
    effective_from: date | None = None
    effective_to: date | None = None
    details: list[PriceListDetailCreate] | None = Field(default=None, min_length=1)


class PriceListResponse(BaseModel):
    id: str
    description: str
    version: int
    effective_from: date
    effective_to: date
    status: PriceListStatus
    created_at: datetime
    updated_at: datetime
    details: list[PriceListDetailResponse]

    model_config = ConfigDict(from_attributes=True)


class ActiveServicePriceResponse(BaseModel):
    price_list_id: str
    version: int
    service_id: int
    service_name: str
    unit: str
    unit_price: Decimal
    effective_from: date
    effective_to: date
