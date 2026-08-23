import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Contract(Base):
    __tablename__ = "contract"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date] = mapped_column(Date, nullable=False)
    payment_terms: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    services: Mapped[list["ContractService"]] = relationship(
        back_populates="contract",
        cascade="all, delete-orphan",
    )
    appendices: Mapped[list["ContractAppendix"]] = relationship(
        back_populates="contract",
        cascade="all, delete-orphan",
    )


class ContractService(Base):
    __tablename__ = "contract_service"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    contract_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contract.id"), nullable=False, index=True
    )
    service_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    service_name: Mapped[str] = mapped_column(String(255), nullable=False)
    service_unit: Mapped[str] = mapped_column(String(100), nullable=False)
    service_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    contract: Mapped[Contract] = relationship(back_populates="services")


class ContractAppendix(Base):
    __tablename__ = "contract_appendix"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    contract_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contract.id"), nullable=False, index=True
    )
    appendix_name: Mapped[str] = mapped_column(String(255), nullable=False)
    change_type: Mapped[str] = mapped_column(String(100), nullable=False)
    new_valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    new_valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    new_payment_terms: Mapped[str | None] = mapped_column(String(255), nullable=True)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    contract: Mapped[Contract] = relationship(back_populates="appendices")
    change_details: Mapped[list["AppendixChangeDetail"]] = relationship(
        back_populates="appendix",
        cascade="all, delete-orphan",
    )


class AppendixChangeDetail(Base):
    __tablename__ = "appendix_change_detail"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    appendix_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contract_appendix.id"), nullable=False, index=True
    )
    service_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    old_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    new_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)

    appendix: Mapped[ContractAppendix] = relationship(back_populates="change_details")


class ContractYearSequence(Base):
    __tablename__ = "contract_year_sequence"

    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_record"
    __table_args__ = (
        UniqueConstraint(
            "endpoint",
            "idempotency_key",
            name="uq_idempotency_endpoint_key",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    endpoint: Mapped[str] = mapped_column(String(100), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now
    )
