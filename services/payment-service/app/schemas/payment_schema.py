from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.payment_model import PaymentStatus


class PaymentPeriodRequest(BaseModel):
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


class PaymentLinePreview(BaseModel):
    service_id: str
    description: str
    quantity: Decimal
    unit_price_snapshot: Decimal
    line_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal


class PaymentPreviewResponse(PaymentPeriodRequest):
    lines: list[PaymentLinePreview]
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal


class PaymentCreate(PaymentPeriodRequest):
    pass


class PaymentUpdate(BaseModel):
    tax_rate: Decimal = Field(ge=0, le=1)


class PaymentLineResponse(PaymentLinePreview):
    model_config = ConfigDict(from_attributes=True)
    id: str


class AdjustmentCreate(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)
    amount: Decimal


class AdjustmentResponse(AdjustmentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    payment_id: str
    status: str
    created_at: datetime


class PaymentResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "payment-001",
                "customer_id": "customer-001",
                "contract_id": "contract-001",
                "period_start": "2026-08-01",
                "period_end": "2026-08-31",
                "subtotal": "1440000.00",
                "tax_amount": "144000.00",
                "total_amount": "1584000.00",
                "status": "DRAFT",
                "approval_instance_id": None,
                "lines": [
                    {
                        "id": "payment-line-001",
                        "service_id": "CONTAINER_20",
                        "description": "20-foot container handling",
                        "quantity": "12.0000",
                        "unit_price_snapshot": "120000.00",
                        "line_amount": "1440000.00",
                        "tax_rate": "0.1000",
                        "tax_amount": "144000.00"
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
