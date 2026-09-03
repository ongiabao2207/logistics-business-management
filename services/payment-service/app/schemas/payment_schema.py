from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator

from app.models.payment_model import PaymentStatus


class ApiModel(BaseModel):
    @field_serializer("*", check_fields=False, when_used="json")
    def serialize_decimal(self, value):
        if not isinstance(value, Decimal):
            return value

        formatted = format(value, "f").rstrip("0").rstrip(".")
        return "0" if formatted in {"", "-0"} else formatted


class PaymentReview(BaseModel):
    decision: Literal["APPROVE", "REJECT"]


class PaymentPeriodRequest(ApiModel):
    customer_id: str = Field(min_length=1, max_length=100)
    contract_id: str = Field(min_length=1, max_length=100)
    period_start: date
    period_end: date
    tax_rate: Decimal = Field(default=Decimal("0.10"), ge=0, le=1)

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self


class PaymentLinePreview(ApiModel):
    service_id: str
    description: str
    confirmed_quantity: Decimal
    billing_quantity: Decimal
    unit_price_snapshot: Decimal
    line_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal


class PaymentPreviewResponse(PaymentPeriodRequest):
    lines: list[PaymentLinePreview]
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal


class PaymentCreateLine(ApiModel):
    model_config = ConfigDict(extra="forbid")

    service_id: str = Field(min_length=1, max_length=100)
    billing_quantity: Decimal = Field(gt=0)


class PaymentCreate(PaymentPeriodRequest):
    lines: list[PaymentCreateLine] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_unique_lines(self):
        if self.lines is not None:
            service_ids = [line.service_id for line in self.lines]
            if len(service_ids) != len(set(service_ids)):
                raise ValueError("Payment lines must have unique service_id values")
        return self


class PaymentLineUpdate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    service_id: str = Field(min_length=1, max_length=100)
    billing_quantity: Decimal | None = Field(default=None, gt=0)
    tax_rate: Decimal | None = Field(default=None, ge=0, le=1)
    remove: bool = False

    @model_validator(mode="after")
    def validate_line_action(self):
        if not self.remove and self.billing_quantity is None:
            raise ValueError(
                "billing_quantity is required unless remove is true"
            )
        return self


class PaymentUpdate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=3, max_length=1000)
    tax_rate: Decimal | None = Field(default=None, ge=0, le=1)
    lines: list[PaymentLineUpdate] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_update(self):
        if self.tax_rate is None and self.lines is None:
            raise ValueError("At least one of tax_rate or lines must be provided")

        if self.lines is not None:
            service_ids = [line.service_id for line in self.lines]
            if len(service_ids) != len(set(service_ids)):
                raise ValueError("Payment lines must have unique service_id values")

        return self


class PaymentLineResponse(PaymentLinePreview):
    model_config = ConfigDict(from_attributes=True)
    id: str


class AdjustmentCreate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    revision_request_id: str = Field(min_length=1, max_length=100)
    adjustment_note: str = Field(min_length=3, max_length=2000)
    tax_rate: Decimal | None = Field(default=None, ge=0, le=1)
    lines: list[PaymentLineUpdate] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_adjustment(self):
        if self.tax_rate is None and self.lines is None:
            raise ValueError("At least one of tax_rate or lines must be provided")
        if self.lines is not None:
            service_ids = [line.service_id for line in self.lines]
            if len(service_ids) != len(set(service_ids)):
                raise ValueError("Adjustment lines must have unique service_id values")
        return self


class AdjustmentResponse(ApiModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    payment_id: str
    revision_request_id: str | None
    adjustment_note: str
    amount: Decimal
    status: str
    change_type: str
    action: str | None
    service_id: str | None
    confirmed_quantity: Decimal | None
    previous_billing_quantity: Decimal | None
    new_billing_quantity: Decimal | None
    previous_tax_rate: Decimal | None
    new_tax_rate: Decimal | None
    created_at: datetime


class PaymentResponse(ApiModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "TT-2026-001",
                "customer_id": "customer-001",
                "contract_id": "contract-001",
                "period_start": "2026-08-01",
                "period_end": "2026-08-31",
                "subtotal": "1440000",
                "tax_amount": "144000",
                "total_amount": "1584000",
                "status": "DRAFT",
                "approval_instance_id": None,
                "lines": [
                    {
                        "id": "payment-line-001",
                        "service_id": "CONTAINER_20",
                        "description": "20-foot container handling",
                        "confirmed_quantity": "12",
                        "billing_quantity": "12",
                        "unit_price_snapshot": "120000",
                        "line_amount": "1440000",
                        "tax_rate": "0.1",
                        "tax_amount": "144000"
                    }
                ],
                "adjustments": [],
                "created_at": "2026-08-22T10:00:00Z",
                "updated_at": "2026-08-22T10:00:00Z"
            }
        },
    )

    id: str
    customer_id: str
    contract_id: str
    period_start: date
    period_end: date
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: PaymentStatus
    approval_instance_id: str | None
    lines: list[PaymentLineResponse]
    adjustments: list[AdjustmentResponse]
    created_at: datetime
    updated_at: datetime
