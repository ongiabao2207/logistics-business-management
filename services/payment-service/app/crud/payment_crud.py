from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.payment_model import (
    Payment,
    PaymentAdjustment,
    PaymentLine,
    PaymentNumberSequence,
    PaymentStatus,
)
from app.schemas.payment_schema import PaymentPreviewResponse


class PaymentCrud:
    def next_payment_id(
        self,
        db: Session,
        year: int,
    ) -> str:
        sequence = db.get(
            PaymentNumberSequence,
            year,
            with_for_update=True,
        )

        if sequence is None:
            sequence = PaymentNumberSequence(year=year, last_number=0)
            db.add(sequence)
            try:
                db.flush()
            except IntegrityError:
                db.rollback()
                sequence = db.get(
                    PaymentNumberSequence,
                    year,
                    with_for_update=True,
                )

        if sequence is None:
            raise RuntimeError("Could not allocate payment number sequence")
        if sequence.last_number >= 999:
            raise ValueError(
                f"Payment number limit for {year} has been reached"
            )

        sequence.last_number += 1
        return f"TT-{year}-{sequence.last_number:03d}"

    def get_by_contract_period(
        self,
        db: Session,
        contract_id: str,
        period_start: date,
        period_end: date,
    ) -> Payment | None:
        return db.scalar(
            select(Payment).where(
                Payment.contract_id == contract_id,
                Payment.period_start == period_start,
                Payment.period_end == period_end,
            )
        )

    def create(
        self,
        db: Session,
        preview: PaymentPreviewResponse,
    ) -> Payment:
        payment = Payment(
            id=self.next_payment_id(db, preview.period_start.year),
            customer_id=preview.customer_id,
            contract_id=preview.contract_id,
            period_start=preview.period_start,
            period_end=preview.period_end,
            subtotal=preview.subtotal,
            tax_amount=preview.tax_amount,
            total_amount=preview.total_amount,
            lines=[
                PaymentLine(**line.model_dump())
                for line in preview.lines
            ],
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        return payment

    def get(
        self,
        db: Session,
        payment_id: str,
    ) -> Payment | None:
        return db.scalar(
            select(Payment).where(
                Payment.id == payment_id,
            )
        )

    def list(
        self,
        db: Session,
        offset: int,
        limit: int,
        contract_id: str | None = None,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> list[Payment]:
        statement = select(Payment)
        if contract_id:
            statement = statement.where(Payment.contract_id == contract_id)
        if period_start:
            statement = statement.where(Payment.period_start == period_start)
        if period_end:
            statement = statement.where(Payment.period_end == period_end)
        statement = statement.order_by(
            Payment.id.desc(),
            Payment.created_at.desc(),
        ).offset(offset).limit(limit)

        return list(db.scalars(statement).all())

    def update_totals(
        self,
        db: Session,
        payment: Payment,
        preview: PaymentPreviewResponse,
        reason: str,
        change_type: str,
        revision_request_id: str | None = None,
    ) -> Payment:
        old_lines = {line.service_id: line for line in payment.lines}
        new_lines = {line.service_id: line for line in preview.lines}

        for service_id in old_lines.keys() | new_lines.keys():
            old_line = old_lines.get(service_id)
            new_line = new_lines.get(service_id)

            if old_line is None:
                action = "ADD"
                amount = new_line.line_amount + new_line.tax_amount
            elif new_line is None:
                action = "REMOVE"
                amount = -(old_line.line_amount + old_line.tax_amount)
            else:
                action = "UPDATE"
                amount = (
                    new_line.line_amount
                    + new_line.tax_amount
                    - old_line.line_amount
                    - old_line.tax_amount
                )

            quantity_changed = (
                old_line is None
                or new_line is None
                or old_line.billing_quantity != new_line.billing_quantity
            )
            tax_changed = (
                old_line is None
                or new_line is None
                or old_line.tax_rate != new_line.tax_rate
            )

            if quantity_changed or tax_changed:
                db.add(
                    PaymentAdjustment(
                        payment_id=payment.id,
                        reason=reason,
                        amount=amount,
                        status="APPLIED",
                        change_type=change_type,
                        action=action,
                        revision_request_id=revision_request_id,
                        service_id=service_id,
                        confirmed_quantity=(
                            new_line.confirmed_quantity
                            if new_line is not None
                            else old_line.confirmed_quantity
                        ),
                        previous_billing_quantity=(
                            old_line.billing_quantity
                            if old_line is not None
                            else None
                        ),
                        new_billing_quantity=(
                            new_line.billing_quantity
                            if new_line is not None
                            else None
                        ),
                        previous_tax_rate=(
                            old_line.tax_rate
                            if old_line is not None
                            else None
                        ),
                        new_tax_rate=(
                            new_line.tax_rate
                            if new_line is not None
                            else None
                        ),
                    )
                )

        payment.subtotal = preview.subtotal
        payment.tax_amount = preview.tax_amount
        payment.total_amount = preview.total_amount
        payment.lines = [
            PaymentLine(**line.model_dump())
            for line in preview.lines
        ]

        db.commit()
        db.refresh(payment)

        return payment

    def submit(
        self,
        db: Session,
        payment: Payment,
        approval_instance_id: str | None,
    ) -> Payment:
        payment.status = PaymentStatus.PENDING_APPROVAL
        payment.approval_instance_id = approval_instance_id

        db.commit()
        db.refresh(payment)

        return payment
