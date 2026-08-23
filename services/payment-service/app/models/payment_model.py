import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PaymentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    REVISION_REQUESTED = "REVISION_REQUESTED"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"
    SIGNED = "SIGNED"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
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

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id: Mapped[str] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), index=True)
    service_id: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4))
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    payment: Mapped[Payment] = relationship(back_populates="adjustments")
