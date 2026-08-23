from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment_model import Payment, PaymentAdjustment, PaymentLine, PaymentStatus
from app.schemas.payment_schema import AdjustmentCreate, PaymentPreviewResponse


class PaymentCrud:
    def create(self, db: Session, preview: PaymentPreviewResponse) -> Payment:
        payment = Payment(
            customer_id=preview.customer_id,
            contract_id=preview.contract_id,
            period_start=preview.period_start,
            period_end=preview.period_end,
            subtotal=preview.subtotal,
            tax_amount=preview.tax_amount,
            total_amount=preview.total_amount,
            lines=[PaymentLine(**line.model_dump()) for line in preview.lines],
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    def get(self, db: Session, payment_id: str) -> Payment | None:
        return db.scalar(select(Payment).where(Payment.id == payment_id))

    def list(self, db: Session, offset: int, limit: int) -> list[Payment]:
        return list(db.scalars(select(Payment).order_by(Payment.created_at.desc()).offset(offset).limit(limit)).all())

    def update_totals(self, db: Session, payment: Payment, preview: PaymentPreviewResponse) -> Payment:
        payment.subtotal = preview.subtotal
        payment.tax_amount = preview.tax_amount
        payment.total_amount = preview.total_amount
        payment.lines = [PaymentLine(**line.model_dump()) for line in preview.lines]
        db.commit()
        db.refresh(payment)
        return payment

    def submit(self, db: Session, payment: Payment, approval_instance_id: str) -> Payment:
        payment.status = PaymentStatus.PENDING_APPROVAL
        payment.approval_instance_id = approval_instance_id
        db.commit()
        db.refresh(payment)
        return payment

    def create_adjustment(self, db: Session, payment: Payment, data: AdjustmentCreate) -> PaymentAdjustment:
        adjustment = PaymentAdjustment(payment_id=payment.id, **data.model_dump())
        db.add(adjustment)
        db.commit()
        db.refresh(adjustment)
        return adjustment
