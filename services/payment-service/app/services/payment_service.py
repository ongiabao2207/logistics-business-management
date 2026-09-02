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

        records = self.production.get_eligible_records(
            contract_id=request.contract_id,
            period_start=request.period_start,
            period_end=request.period_end,
        )

        if not records:
            raise PaymentError(
                "No production data exists for the payment period",
                422,
            )

        lines: list[PaymentLinePreview] = []

        for record in records:
            record_is_outside_period = (
                record.period_start < request.period_start
                or record.period_end > request.period_end
            )

            if record_is_outside_period:
                raise PaymentError(
                    "Production data does not belong "
                    "to the payment period",
                    422,
                )

            if record.status not in {
                "CONFIRMED",
                "RECONCILED",
            }:
                raise PaymentError(
                    "Production data must be "
                    "confirmed or reconciled",
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

        preview = self.preview(request)

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
    ) -> list[Payment]:
        return self.crud.list(
            db=db,
            offset=offset,
            limit=limit,
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
        current_tax_rate = (
            payment.lines[0].tax_rate
            if payment.lines
            else Decimal("0.10")
        )
        tax_rate = (
            request.tax_rate
            if request.tax_rate is not None
            else current_tax_rate
        )

        draft_lines = {
            line.service_id: {
                "description": line.description,
                "confirmed_quantity": line.confirmed_quantity,
                "billing_quantity": line.billing_quantity,
                "unit_price": line.unit_price_snapshot,
                "tax_rate": (
                    line.tax_rate
                    if request.tax_rate is None
                    else request.tax_rate
                ),
            }
            for line in payment.lines
        }

        production_records = None
        for requested_line in request.lines or []:
            service_id = requested_line.service_id

            if requested_line.remove:
                if service_id not in draft_lines:
                    raise PaymentError(
                        f"Payment line {service_id} was not found",
                        404,
                    )
                del draft_lines[service_id]
                continue

            if service_id in draft_lines:
                current_line = draft_lines[service_id]
                current_line["billing_quantity"] = (
                    requested_line.billing_quantity
                )
                if requested_line.tax_rate is not None:
                    current_line["tax_rate"] = requested_line.tax_rate
                continue

            if production_records is None:
                production_records = self.production.get_eligible_records(
                    contract_id=payment.contract_id,
                    period_start=payment.period_start,
                    period_end=payment.period_end,
                )
            record = next(
                (
                    item
                    for item in production_records
                    if item.service_id == service_id
                    and item.status in {"CONFIRMED", "RECONCILED"}
                ),
                None,
            )
            if record is None:
                raise PaymentError(
                    f"Service {service_id} has no confirmed production "
                    "record for the payment period",
                    422,
                )
            try:
                unit_price = self.prices.get_effective_price(
                    contract_id=payment.contract_id,
                    service_id=service_id,
                    business_date=payment.period_end,
                )
            except LookupError as exc:
                raise PaymentError(str(exc), 422) from exc

            draft_lines[service_id] = {
                "description": record.description,
                "confirmed_quantity": record.quantity,
                "billing_quantity": requested_line.billing_quantity,
                "unit_price": unit_price,
                "tax_rate": (
                    requested_line.tax_rate
                    if requested_line.tax_rate is not None
                    else tax_rate
                ),
            }

        if not draft_lines:
            raise PaymentError(
                "Payment must retain at least one service line",
                422,
            )

        calculated_lines: list[PaymentLinePreview] = []

        for service_id, values in draft_lines.items():
            description = values["description"]
            confirmed_quantity = values["confirmed_quantity"]
            billing_quantity = values["billing_quantity"]
            unit_price = values["unit_price"]
            line_tax_rate = values["tax_rate"]
            if billing_quantity > confirmed_quantity:
                raise PaymentError(
                    f"Billing quantity for {service_id} must not exceed "
                    "the confirmed production quantity",
                    422,
                )

            line_amount = (
                billing_quantity * unit_price
            ).quantize(
                MONEY,
                rounding=ROUND_HALF_UP,
            )
            applied_tax_rate = (
                line_tax_rate
                if line_tax_rate is not None
                else tax_rate
            )
            line_tax_amount = (
                line_amount * applied_tax_rate
            ).quantize(
                MONEY,
                rounding=ROUND_HALF_UP,
            )

            calculated_lines.append(
                PaymentLinePreview(
                    service_id=service_id,
                    description=description,
                    confirmed_quantity=confirmed_quantity,
                    billing_quantity=billing_quantity,
                    unit_price_snapshot=unit_price,
                    line_amount=line_amount,
                    tax_rate=applied_tax_rate,
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
            tax_rate=tax_rate,
            lines=calculated_lines,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=(subtotal + tax_amount).quantize(
                MONEY,
                rounding=ROUND_HALF_UP,
            ),
        )

        current_line_values = {
            line.service_id: (
                line.billing_quantity,
                line.tax_rate,
            )
            for line in payment.lines
        }
        updated_line_values = {
            line.service_id: (
                line.billing_quantity,
                line.tax_rate,
            )
            for line in calculated_lines
        }
        if (
            change_type == "REVISION_ADJUSTMENT"
            and current_line_values == updated_line_values
        ):
            raise PaymentError(
                "Adjustment must change at least one payment line",
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

        if payment.status != PaymentStatus.REJECTED:
            raise PaymentError(
                "Payment can only be adjusted after rejection",
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
                lines=data.lines,
            ),
            change_type="REVISION_ADJUSTMENT",
            revision_request_id=data.revision_request_id,
        )

        self.events.publish(
            "PaymentAdjustmentApplied",
            {
                "payment_id": payment.id,
                "revision_request_id": data.revision_request_id,
            },
        )

        return updated
