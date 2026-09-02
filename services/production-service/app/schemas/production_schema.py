from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.production_model import ProductionPeriodStatus


class ProductionReview(BaseModel):
    decision: Literal["APPROVE", "REJECT"]


class ProductionDetailInput(BaseModel):
    service_code: str = Field(min_length=1, max_length=64)
    recorded_date: date
    quantity: Decimal = Field(gt=0, max_digits=18, decimal_places=3)
    unit: str = Field(min_length=1, max_length=32)
    notes: str | None = Field(default=None, max_length=4000)


class ProductionDetailResponse(ProductionDetailInput):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ProductionPeriodCreate(BaseModel):
    customer_id: str = Field(min_length=1, max_length=64)
    contract_id: str = Field(min_length=1, max_length=64)
    period_name: str = Field(min_length=1, max_length=255)
    from_date: date
    to_date: date
    details: list[ProductionDetailInput] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_dates(self) -> "ProductionPeriodCreate":
        if self.from_date > self.to_date:
            raise ValueError("from_date must not be later than to_date")
        return self


class ProductionDetailsReplace(BaseModel):
    details: list[ProductionDetailInput] = Field(min_length=1)


class ProductionPeriodResponse(BaseModel):
    id: int
    customer_id: str
    contract_id: str
    period_name: str
    from_date: date
    to_date: date
    status: ProductionPeriodStatus
    locked_at: datetime | None
    locked_by: str | None
    created_at: datetime
    updated_at: datetime
    details: list[ProductionDetailResponse] = []
    model_config = ConfigDict(from_attributes=True)


class OverlapCheckRequest(BaseModel):
    customer_id: str = Field(min_length=1, max_length=64)
    contract_id: str = Field(min_length=1, max_length=64)
    from_date: date
    to_date: date

    @model_validator(mode="after")
    def validate_dates(self) -> "OverlapCheckRequest":
        if self.from_date > self.to_date:
            raise ValueError("from_date must not be later than to_date")
        return self


class OverlapCheckResponse(BaseModel):
    overlaps: bool
    conflicting_period_ids: list[int] = []


class ServiceQuantityTotal(BaseModel):
    service_code: str
    unit: str
    quantity: Decimal


class ProductionPeriodDetailResponse(ProductionPeriodResponse):
    totals: list[ServiceQuantityTotal]
