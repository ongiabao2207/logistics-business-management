from datetime import date
from decimal import Decimal

import pytest

from app.api.dependencies import build_payment_service
from app.models.payment_model import PaymentNumberSequence, PaymentStatus
from app.schemas.payment_schema import (
    PaymentCreate,
    PaymentPeriodRequest,
    PaymentUpdate,
)
from app.services.payment_service import PaymentError


def request(
    contract_id: str = "contract-001",
) -> PaymentPeriodRequest:
    return PaymentPeriodRequest(
        customer_id="customer-001",
        contract_id=contract_id,
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 31),
        tax_rate=Decimal("0.10"),
    )


def test_preview_calculates_amounts_and_price_snapshot():
    service = build_payment_service()

    preview = service.preview(
        request()
    )

    assert (
        preview.lines[0].confirmed_quantity
        == Decimal("12")
    )
    assert preview.lines[0].billing_quantity == Decimal("12")
    assert (
        preview.lines[0].unit_price_snapshot
        == Decimal("120000")
    )
    assert (
        preview.subtotal
        == Decimal("1440000.00")
    )
    assert (
        preview.tax_amount
        == Decimal("144000.00")
    )
    assert (
        preview.total_amount
        == Decimal("1584000.00")
    )
    serialized = preview.model_dump(mode="json")
    assert serialized["subtotal"] == "1440000"
    assert serialized["tax_rate"] == "0.1"
    assert serialized["lines"][0]["confirmed_quantity"] == "12"


def test_create_rejects_duplicate_contract_period(
    db_session,
):
    service = build_payment_service()

    payment_request = PaymentCreate(
        **request().model_dump()
    )

    first_payment = service.create(
        db_session,
        payment_request,
    )

    assert first_payment.id is not None

    with pytest.raises(
        PaymentError,
        match="already exists",
    ) as error:
        service.create(
            db_session,
            payment_request,
        )

    assert error.value.status_code == 409


def test_payment_ids_use_yearly_three_digit_sequence(db_session):
    service = build_payment_service()

    first = service.create(
        db_session,
        PaymentCreate(**request("contract-sequence-a").model_dump()),
    )
    second = service.create(
        db_session,
        PaymentCreate(**request("contract-sequence-b").model_dump()),
    )
    next_year_request = PaymentCreate(
        customer_id="customer-001",
        contract_id="contract-sequence-c",
        period_start=date(2027, 1, 1),
        period_end=date(2027, 1, 31),
        tax_rate=Decimal("0.10"),
    )
    next_year = service.create(db_session, next_year_request)

    assert first.id == "TT-2026-001"
    assert second.id == "TT-2026-002"
    assert next_year.id == "TT-2027-001"


def test_payment_id_rejects_more_than_999_per_year(db_session):
    service = build_payment_service()
    db_session.add(PaymentNumberSequence(year=2026, last_number=999))
    db_session.commit()

    with pytest.raises(PaymentError, match="limit for 2026") as error:
        service.create(
            db_session,
            PaymentCreate(**request("contract-sequence-limit").model_dump()),
        )

    assert error.value.status_code == 409


@pytest.mark.parametrize(
    ("contract_id", "message"),
    [
        (
            "expired-contract",
            "not valid",
        ),
        (
            "no-production",
            "No production data",
        ),
        (
            "unconfirmed-production",
            "confirmed or reconciled",
        ),
        (
            "no-price",
            "No applicable price",
        ),
    ],
)
def test_preview_rejects_invalid_dependencies(
    contract_id,
    message,
):
    service = build_payment_service()

    with pytest.raises(
        PaymentError,
        match=message,
    ):
        service.preview(
            request(contract_id)
        )


def test_create_snapshots_price_and_submit_starts_direct_review(
    db_session,
):
    service = build_payment_service()

    payment = service.create(
        db_session,
        PaymentCreate(
            **request().model_dump()
        ),
    )

    assert payment.status == PaymentStatus.DRAFT
    assert (
        payment.lines[0].unit_price_snapshot
        == Decimal("120000.00")
    )

    submitted_payment = service.submit(
        db_session,
        payment.id,
    )

    assert (
        submitted_payment.status
        == PaymentStatus.PENDING_APPROVAL
    )
    assert submitted_payment.approval_instance_id is None


def test_submit_is_idempotency_guarded(
    db_session,
):
    service = build_payment_service()

    payment = service.create(
        db_session,
        PaymentCreate(
            **request().model_dump()
        ),
    )

    service.submit(
        db_session,
        payment.id,
    )

    with pytest.raises(
        PaymentError,
        match="cannot be submitted",
    ) as error:
        service.submit(
            db_session,
            payment.id,
        )

    assert error.value.status_code == 409


def test_approved_payment_cannot_be_recalculated(
    db_session,
):
    service = build_payment_service()

    payment = service.create(
        db_session,
        PaymentCreate(
            **request().model_dump()
        ),
    )

    payment.status = PaymentStatus.APPROVED
    db_session.commit()

    with pytest.raises(
        PaymentError,
        match="cannot be edited",
    ) as error:
        service.recalculate(
            db_session,
            payment.id,
            Decimal("0.08"),
        )

    assert error.value.status_code == 409


def test_update_draft_changes_tax_without_changing_confirmed_quantity(
    db_session,
):
    service = build_payment_service()
    payment = service.create(
        db_session,
        PaymentCreate(**request().model_dump()),
    )

    updated = service.update_draft(
        db=db_session,
        payment_id=payment.id,
        request=PaymentUpdate(
            reason="Correct tax rate",
            tax_rate=Decimal("0.08"),
        ),
    )

    assert updated.status == PaymentStatus.DRAFT
    assert updated.lines[0].confirmed_quantity == Decimal("12.0000")
    assert updated.lines[0].billing_quantity == Decimal("12.0000")
    assert updated.lines[0].unit_price_snapshot == Decimal("120000.00")
    assert updated.subtotal == Decimal("1440000.00")
    assert updated.tax_amount == Decimal("115200.00")
    assert updated.total_amount == Decimal("1555200.00")
    assert len(updated.adjustments) == 1
    assert updated.adjustments[0].previous_billing_quantity == Decimal("12.0000")
    assert updated.adjustments[0].new_billing_quantity == Decimal("12.0000")
    assert updated.adjustments[0].previous_tax_rate == Decimal("0.1000")
    assert updated.adjustments[0].new_tax_rate == Decimal("0.0800")


def test_submitted_payment_cannot_be_updated(
    db_session,
):
    service = build_payment_service()
    payment = service.create(
        db_session,
        PaymentCreate(**request().model_dump()),
    )
    service.submit(db_session, payment.id)

    with pytest.raises(
        PaymentError,
        match="cannot be edited",
    ) as error:
        service.update_draft(
            db=db_session,
            payment_id=payment.id,
            request=PaymentUpdate(
                reason="Correct tax rate",
                tax_rate=Decimal("0.08"),
            ),
        )

    assert error.value.status_code == 409


def test_revision_requested_payment_requires_adjustment_api(
    db_session,
):
    service = build_payment_service()
    payment = service.create(
        db_session,
        PaymentCreate(**request().model_dump()),
    )
    payment.status = PaymentStatus.REVISION_REQUESTED
    db_session.commit()

    with pytest.raises(PaymentError, match="cannot be edited") as error:
        service.update_draft(
            db=db_session,
            payment_id=payment.id,
            request=PaymentUpdate(
                reason="Must use adjustment workflow",
                tax_rate=Decimal("0.08"),
            ),
        )

    assert error.value.status_code == 409
