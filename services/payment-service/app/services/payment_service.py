from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.clients.approvals import ApprovalClient
from app.clients.contracts import ContractClient
from app.clients.prices import PriceClient
from app.clients.production import ProductionClient
from app.crud.payment_crud import PaymentCrud
from app.messaging.producer import EventPublisher
from app.models.payment_model import Payment, PaymentStatus
from app.schemas.payment_schema import (
    AdjustmentCreate,
    PaymentCreate,
    PaymentLinePreview,
    PaymentPeriodRequest,
    PaymentPreviewResponse,
)


MONEY = Decimal("0.01")


class PaymentError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class PaymentService:
    def __init__(
        self,
        crud: PaymentCrud,
        contracts: ContractClient,
        production: ProductionClient,
        prices: PriceClient,
        approvals: ApprovalClient,
        events: EventPublisher,
    ):
        self.crud = crud
        self.contracts = contracts
        self.production = production
        self.prices = prices
        self.approvals = approvals
        self.events = events

    def preview(self, request: PaymentPeriodRequest) -> PaymentPreviewResponse:
        try:
            contract = self.contracts.get_contract(request.contract_id, request.customer_id)
        except LookupError as exc:
            raise PaymentError(str(exc), 404) from exc
        if contract.status != "ACTIVE" or request.period_start < contract.valid_from or request.period_end > contract.valid_to:
            raise PaymentError("Contract is not valid for the payment period", 422)

        records = self.production.get_eligible_records(request.contract_id, request.period_start, request.period_end)
        if not records:
            raise PaymentError("No production data exists for the payment period", 422)

        lines: list[PaymentLinePreview] = []
        for record in records:
            if record.period_start < request.period_start or record.period_end > request.period_end:
                raise PaymentError("Production data does not belong to the payment period", 422)
            if record.status not in {"CONFIRMED", "RECONCILED"}:
                raise PaymentError("Production data must be confirmed or reconciled", 422)
            try:
                unit_price = self.prices.get_effective_price(request.contract_id, record.service_id, request.period_end)
            except LookupError as exc:
                raise PaymentError(str(exc), 422) from exc
            line_amount = (record.quantity * unit_price).quantize(MONEY, rounding=ROUND_HALF_UP)
            tax_amount = (line_amount * request.tax_rate).quantize(MONEY, rounding=ROUND_HALF_UP)
            lines.append(PaymentLinePreview(
                service_id=record.service_id,
                description=record.description,
                quantity=record.quantity,
                unit_price_snapshot=unit_price,
                line_amount=line_amount,
                tax_rate=request.tax_rate,
                tax_amount=tax_amount,
            ))

        subtotal = sum((line.line_amount for line in lines), Decimal("0")).quantize(MONEY)
        tax_amount = sum((line.tax_amount for line in lines), Decimal("0")).quantize(MONEY)
        return PaymentPreviewResponse(**request.model_dump(), lines=lines, subtotal=subtotal, tax_amount=tax_amount, total_amount=subtotal + tax_amount)

    def create(self, db: Session, request: PaymentCreate) -> Payment:
        payment = self.crud.create(db, self.preview(request))
        self.events.publish("PaymentStatementCreated", {"payment_id": payment.id, "total_amount": str(payment.total_amount)})
        return payment

    def get(self, db: Session, payment_id: str) -> Payment:
        payment = self.crud.get(db, payment_id)
        if payment is None:
            raise PaymentError("Payment statement was not found", 404)
        return payment

    def list(self, db: Session, offset: int, limit: int) -> list[Payment]:
        return self.crud.list(db, offset, limit)

    def recalculate(self, db: Session, payment_id: str, tax_rate: Decimal) -> Payment:
        payment = self.get(db, payment_id)
        if payment.status in {PaymentStatus.APPROVED, PaymentStatus.SIGNED}:
            raise PaymentError("Approved or signed payment statements are immutable", 409)
        request = PaymentPeriodRequest(
            customer_id=payment.customer_id,
            contract_id=payment.contract_id,
            period_start=payment.period_start,
            period_end=payment.period_end,
            tax_rate=tax_rate,
        )
        return self.crud.update_totals(db, payment, self.preview(request))

    def submit(self, db: Session, payment_id: str) -> Payment:
        payment = self.get(db, payment_id)
        if payment.status not in {PaymentStatus.DRAFT, PaymentStatus.REVISION_REQUESTED}:
            raise PaymentError(f"Payment in {payment.status.value} cannot be submitted", 409)
        if not payment.lines or payment.total_amount < 0:
            raise PaymentError("Payment must have service lines and a non-negative total", 422)
        approval_id = self.approvals.create_workflow(payment.id, "PAYMENT")
        submitted = self.crud.submit(db, payment, approval_id)
        self.events.publish("PaymentSubmitted", {"payment_id": payment.id, "approval_instance_id": approval_id})
        return submitted

    def adjust(self, db: Session, payment_id: str, data: AdjustmentCreate):
        payment = self.get(db, payment_id)
        adjustment = self.crud.create_adjustment(db, payment, data)
        self.events.publish("PaymentAdjustmentCreated", {"payment_id": payment.id, "adjustment_id": adjustment.id})
        return adjustment
