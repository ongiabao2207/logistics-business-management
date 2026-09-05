from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.clients.contracts import ContractClient
from app.clients.prices import PriceClient
from app.clients.production import ProductionClient
from app.crud.payment_crud import PaymentCrud
from app.messaging.producer import EventPublisher
from app.models.payment_model import (
    Payment,
    PaymentStatus,
)
from app.schemas.payment_schema import (
    AdjustmentCreate,
    PaymentCreate,
    PaymentLinePreview,
    PaymentPeriodRequest,
    PaymentPreviewResponse,
    PaymentUpdate,
)


MONEY = Decimal("0.01")


class PaymentError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
    ):
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
        events: EventPublisher,
    ):
        self.crud = crud
        self.contracts = contracts
        self.production = production
        self.prices = prices
        self.events = events

    def preview(
        self,
        request: PaymentPeriodRequest,
    ) -> PaymentPreviewResponse:
        try:
            contract = self.contracts.get_contract(
                contract_id=request.contract_id,
                customer_id=request.customer_id,
            )
        except ConnectionError as exc:
            raise PaymentError(str(exc), 503) from exc
        except LookupError as exc:
            raise PaymentError(
                str(exc),
                404,
            ) from exc

        contract_is_invalid = (
            contract.status != "ACTIVE"
            or request.period_start < contract.valid_from
            or request.period_end > contract.valid_to
        )

        if contract_is_invalid:
            raise PaymentError(
                "Contract is not valid for the payment period",
                422,
            )

        try:
            records = self.production.get_eligible_records(
                contract_id=request.contract_id,
                period_start=request.period_start,
                period_end=request.period_end,
            )
        except ConnectionError as exc:
            raise PaymentError(str(exc), 503) from exc

        if not records:
            raise PaymentError(
                "No production data exists for the payment period",
                422,
            )

        lines: list[PaymentLinePreview] = []

        for record in records:
            record_is_different_period = (
                record.period_start != request.period_start
                or record.period_end != request.period_end
            )

            if record_is_different_period:
                raise PaymentError(
                    "Production data does not belong "
                    "to the payment period",
                    422,
                )

            if record.status != "LOCKED":
                raise PaymentError(
                    "Kỳ sản lượng phải được khóa trước khi lập bảng thanh toán",
                    422,
                )

            if record.quantity <= 0:
                raise PaymentError(
                    "Confirmed production quantity must be positive",
                    422,
                )

            try:
                unit_price = self.prices.get_effective_price(
                    contract_id=request.contract_id,
                    service_id=record.service_id,
                    business_date=request.period_end,
                )
            except ConnectionError as exc:
                raise PaymentError(str(exc), 503) from exc
            except LookupError as exc:
                raise PaymentError(
                    str(exc),
                    422,
                ) from exc

            if unit_price < 0:
                raise PaymentError(
                    "Applicable unit price must not be negative",
                    422,
                )

            line_amount = (
                record.quantity * unit_price
            ).quantize(
                MONEY,
                rounding=ROUND_HALF_UP,
            )

            tax_amount = (
                line_amount * request.tax_rate
            ).quantize(
                MONEY,
                rounding=ROUND_HALF_UP,
            )

            lines.append(
                PaymentLinePreview(
                    service_id=record.service_id,
                    description=record.description,
                    confirmed_quantity=record.quantity,
                    billing_quantity=record.quantity,
                    unit_price_snapshot=unit_price,
                    line_amount=line_amount,
                    tax_rate=request.tax_rate,
                    tax_amount=tax_amount,
                )
            )

        subtotal = sum(
            (
                line.line_amount
                for line in lines
            ),
            Decimal("0"),
        ).quantize(
            MONEY,
            rounding=ROUND_HALF_UP,
        )

        total_tax_amount = sum(
            (
                line.tax_amount
                for line in lines
            ),
            Decimal("0"),
        ).quantize(
            MONEY,
            rounding=ROUND_HALF_UP,
        )

        total_amount = (
            subtotal + total_tax_amount
        ).quantize(
            MONEY,
            rounding=ROUND_HALF_UP,
        )

        return PaymentPreviewResponse(
            **request.model_dump(),
            lines=lines,
            subtotal=subtotal,
            tax_amount=total_tax_amount,
            total_amount=total_amount,
        )

    def create(
        self,
        db: Session,
        request: PaymentCreate,
    ) -> Payment:
        existing_payment = (
            self.crud.get_by_contract_period(
                db=db,
                contract_id=request.contract_id,
                period_start=request.period_start,
                period_end=request.period_end,
            )
        )

        if existing_payment is not None:
            raise PaymentError(
                "A payment statement already exists "
                "for this contract and payment period",
                409,
            )

        preview = self.preview(PaymentPeriodRequest(**request.model_dump()))

        try:
            payment = self.crud.create(
                db=db,
                preview=preview,
            )
        except ValueError as exc:
            raise PaymentError(str(exc), 409) from exc

        self.events.publish(
            "PaymentStatementCreated",
            {
                "payment_id": payment.id,
                "total_amount": str(
                    payment.total_amount
                ),
                "recipient_role": "ROLE_ACCOUNTANT",
                "title": "Hồ sơ thanh toán mới đã được tạo",
                "content": f"Hồ sơ thanh toán {payment.id} đã sẵn sàng để xử lý.",
                "reference_type": "PAYMENT",
                "reference_id": payment.id,
            },
        )

        return payment

    def get(
        self,
        db: Session,
        payment_id: str,
    ) -> Payment:
        payment = self.crud.get(
            db=db,
            payment_id=payment_id,
        )

        if payment is None:
            raise PaymentError(
                "Payment statement was not found",
                404,
            )

        return payment

    def list(
        self,
        db: Session,
        offset: int,
        limit: int,
        contract_id: str | None = None,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> list[Payment]:
        return self.crud.list(
            db=db,
            offset=offset,
            limit=limit,
            contract_id=contract_id,
            period_start=period_start,
            period_end=period_end,
        )

    def recalculate(
        self,
        db: Session,
        payment_id: str,
        tax_rate: Decimal,
    ) -> Payment:
        return self.update_draft(
            db=db,
            payment_id=payment_id,
            request=PaymentUpdate(
                reason="Tax rate recalculation",
                tax_rate=tax_rate,
            ),
        )

    def update_draft(
        self,
        db: Session,
        payment_id: str,
        request: PaymentUpdate,
    ) -> Payment:
        payment = self.get(
            db=db,
            payment_id=payment_id,
        )

        if payment.status != PaymentStatus.DRAFT:
            raise PaymentError(
                f"Payment in {payment.status.value} "
                "cannot be edited",
                409,
            )

        return self._apply_controlled_update(
            db=db,
            payment=payment,
            request=request,
            change_type="DRAFT_EDIT",
        )

    def _apply_controlled_update(
        self,
        db: Session,
        payment: Payment,
        request: PaymentUpdate,
        change_type: str,
        revision_request_id: str | None = None,
    ) -> Payment:
        if not payment.lines:
            raise PaymentError(
                "Payment must retain at least one service line",
                422,
            )

        calculated_lines: list[PaymentLinePreview] = []

        for line in payment.lines:
            billing_quantity = line.confirmed_quantity
            line_amount = (
                billing_quantity * line.unit_price_snapshot
            ).quantize(
                MONEY,
                rounding=ROUND_HALF_UP,
            )
            line_tax_amount = (
                line_amount * request.tax_rate
            ).quantize(
                MONEY,
                rounding=ROUND_HALF_UP,
            )

            calculated_lines.append(
                PaymentLinePreview(
                    service_id=line.service_id,
                    description=line.description,
                    confirmed_quantity=line.confirmed_quantity,
                    billing_quantity=billing_quantity,
                    unit_price_snapshot=line.unit_price_snapshot,
                    line_amount=line_amount,
                    tax_rate=request.tax_rate,
                    tax_amount=line_tax_amount,
                )
            )

        subtotal = sum(
            (line.line_amount for line in calculated_lines),
            Decimal("0"),
        ).quantize(MONEY, rounding=ROUND_HALF_UP)
        tax_amount = sum(
            (line.tax_amount for line in calculated_lines),
            Decimal("0"),
        ).quantize(MONEY, rounding=ROUND_HALF_UP)

        updated_preview = PaymentPreviewResponse(
            customer_id=payment.customer_id,
            contract_id=payment.contract_id,
            period_start=payment.period_start,
            period_end=payment.period_end,
            tax_rate=request.tax_rate,
            lines=calculated_lines,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=(subtotal + tax_amount).quantize(
                MONEY,
                rounding=ROUND_HALF_UP,
            ),
        )

        if (
            change_type == "REVISION_ADJUSTMENT"
            and all(line.tax_rate == request.tax_rate for line in payment.lines)
        ):
            raise PaymentError(
                "Adjustment must change the tax rate",
                422,
            )

        return self.crud.update_totals(
            db=db,
            payment=payment,
            preview=updated_preview,
            reason=request.reason,
            change_type=change_type,
            revision_request_id=revision_request_id,
        )

    def submit(
        self,
        db: Session,
        payment_id: str,
    ) -> Payment:
        payment = self.get(
            db=db,
            payment_id=payment_id,
        )

        if payment.status not in {
            PaymentStatus.DRAFT,
            PaymentStatus.REVISION_REQUESTED,
        }:
            raise PaymentError(
                f"Payment in {payment.status.value} "
                "cannot be submitted",
                409,
            )

        if not payment.lines:
            raise PaymentError(
                "Payment must have at least "
                "one service line",
                422,
            )

        if payment.total_amount < 0:
            raise PaymentError(
                "Payment total amount "
                "must not be negative",
                422,
            )

        submitted = self.crud.submit(
            db=db,
            payment=payment,
            approval_instance_id=None,
        )

        self.events.publish(
            "PaymentSubmitted",
            {
                "payment_id": submitted.id,
                "approval_instance_id": None,
                "recipient_role": "ROLE_DIRECTOR",
                "title": "Hồ sơ thanh toán chờ phê duyệt",
                "content": f"Hồ sơ thanh toán {submitted.id} đang chờ phê duyệt.",
                "reference_type": "PAYMENT",
                "reference_id": submitted.id,
            },
        )

        return submitted

    def review(self, db: Session, payment_id: str, decision: str) -> Payment:
        payment = self.get(db, payment_id)
        if payment.status != PaymentStatus.PENDING_APPROVAL:
            raise PaymentError("Only pending payments can be reviewed", 409)
        payment.status = PaymentStatus.APPROVED if decision == "APPROVE" else PaymentStatus.REJECTED
        db.commit()
        db.refresh(payment)
        return payment

    def adjust(
        self,
        db: Session,
        payment_id: str,
        data: AdjustmentCreate,
    ) -> Payment:
        payment = self.get(
            db=db,
            payment_id=payment_id,
        )

        if payment.status not in {
            PaymentStatus.REJECTED,
            PaymentStatus.REVISION_REQUESTED,
        }:
            raise PaymentError(
                "Payment can only be adjusted after rejection or a revision request",
                409,
            )

        if any(
            item.revision_request_id == data.revision_request_id
            for item in payment.adjustments
        ):
            raise PaymentError(
                "This approval revision request has already been applied",
                409,
            )

        updated = self._apply_controlled_update(
            db=db,
            payment=payment,
            request=PaymentUpdate(
                reason=data.adjustment_note,
                tax_rate=data.tax_rate,
            ),
            change_type="REVISION_ADJUSTMENT",
            revision_request_id=data.revision_request_id,
        )

        self.events.publish(
            "PaymentAdjustmentApplied",
            {
                "payment_id": payment.id,
                "revision_request_id": data.revision_request_id,
                "recipient_role": "ROLE_ACCOUNTANT",
                "title": "Hồ sơ thanh toán đã được điều chỉnh",
                "content": f"Hồ sơ thanh toán {payment.id} đã có điều chỉnh mới.",
                "reference_type": "PAYMENT",
                "reference_id": payment.id,
            },
        )

        return self.submit(db, updated.id)
