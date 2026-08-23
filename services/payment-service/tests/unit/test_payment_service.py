from datetime import date
from decimal import Decimal

import pytest

from app.api.dependencies import get_payment_service
from app.models.payment_model import PaymentStatus
from app.schemas.payment_schema import PaymentCreate, PaymentPeriodRequest
from app.services.payment_service import PaymentError


def request(contract_id: str = "contract-001") -> PaymentPeriodRequest:
    return PaymentPeriodRequest(
        customer_id="customer-001",
        contract_id=contract_id,
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 31),
        tax_rate=Decimal("0.10"),
    )


def test_preview_calculates_amounts_and_price_snapshot():
    preview = get_payment_service().preview(request())

    assert preview.lines[0].quantity == Decimal("12")
    assert preview.lines[0].unit_price_snapshot == Decimal("120000")
    assert preview.subtotal == Decimal("1440000.00")
    assert preview.tax_amount == Decimal("144000.00")
    assert preview.total_amount == Decimal("1584000.00")


@pytest.mark.parametrize(
    ("contract_id", "message"),
    [
        ("expired-contract", "not valid"),
        ("no-production", "No production data"),
        ("unconfirmed-production", "confirmed or reconciled"),
        ("no-price", "No applicable price"),
    ],
)
def test_preview_rejects_invalid_dependencies(contract_id, message):
    with pytest.raises(PaymentError, match=message):
        get_payment_service().preview(request(contract_id))


def test_create_snapshots_price_and_submit_starts_approval(db_session):
    service = get_payment_service()
    payment = service.create(db_session, PaymentCreate(**request().model_dump()))

    assert payment.status == PaymentStatus.DRAFT
    assert payment.lines[0].unit_price_snapshot == Decimal("120000.00")

    submitted = service.submit(db_session, payment.id)
    assert submitted.status == PaymentStatus.PENDING_APPROVAL
    assert submitted.approval_instance_id.startswith("approval-")


def test_submit_is_idempotency_guarded(db_session):
    service = get_payment_service()
    payment = service.create(db_session, PaymentCreate(**request().model_dump()))
    service.submit(db_session, payment.id)

    with pytest.raises(PaymentError, match="cannot be submitted"):
        service.submit(db_session, payment.id)


def test_approved_payment_cannot_be_recalculated(db_session):
    service = get_payment_service()
    payment = service.create(db_session, PaymentCreate(**request().model_dump()))
    payment.status = PaymentStatus.APPROVED
    db_session.commit()

    with pytest.raises(PaymentError, match="immutable"):
        service.recalculate(db_session, payment.id, Decimal("0.08"))
