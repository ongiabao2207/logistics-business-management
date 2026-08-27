import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, UniqueConstraint, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PaymentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    REVISION_REQUESTED = "REVISION_REQUESTED"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"
    SIGNED = "SIGNED"


class PaymentNumberSequence(Base):
    __tablename__ = "payment_number_sequences"
    __table_args__ = (
        CheckConstraint(
            "last_number >= 0 AND last_number <= 999",
            name="ck_payment_number_sequences_range",
        ),
    )

    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint(
            "contract_id",
            "period_start",
            "period_end",
            name="uq_payments_contract_period",
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(100), index=True)
    contract_id: Mapped[str] = mapped_column(String(100), index=True)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.DRAFT)
    approval_instance_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lines: Mapped[list["PaymentLine"]] = relationship(
        back_populates="payment", cascade="all, delete-orphan", lazy="selectin"
    )
    adjustments: Mapped[list["PaymentAdjustment"]] = relationship(
        back_populates="payment", cascade="all, delete-orphan", lazy="selectin"
    )


class PaymentLine(Base):
    __tablename__ = "payment_lines"
    __table_args__ = (
        CheckConstraint(
            "confirmed_quantity > 0",
            name="ck_payment_lines_confirmed_quantity_positive",
        ),
        CheckConstraint(
            "billing_quantity > 0 AND billing_quantity <= confirmed_quantity",
            name="ck_payment_lines_billing_quantity_range",
        ),
        CheckConstraint(
            "unit_price_snapshot >= 0",
            name="ck_payment_lines_unit_price_non_negative",
        ),
        CheckConstraint(
            "tax_rate >= 0 AND tax_rate <= 1",
            name="ck_payment_lines_tax_rate_range",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id: Mapped[str] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), index=True)
    service_id: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255))
    confirmed_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    billing_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    line_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))

    payment: Mapped[Payment] = relationship(back_populates="lines")


class PaymentAdjustment(Base):
    __tablename__ = "payment_adjustments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id: Mapped[str] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), index=True)
    reason: Mapped[str] = mapped_column(Text)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    status: Mapped[str] = mapped_column(String(30), default="DRAFT")
    change_type: Mapped[str] = mapped_column(String(30), default="MANUAL_AMOUNT")
    action: Mapped[str | None] = mapped_column(String(20), nullable=True)
    revision_request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    service_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confirmed_quantity: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    previous_billing_quantity: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    new_billing_quantity: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    previous_tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    new_tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    payment: Mapped[Payment] = relationship(back_populates="adjustments")

    @property
    def adjustment_note(self) -> str:
        return self.reason
