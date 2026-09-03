from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
import re

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.clients.contract_client import ContractClient
from app.crud import production_crud
from app.messaging.producer import record_event
from app.models.production_model import ProductionDetail, ProductionPeriod, ProductionPeriodStatus
from app.schemas.production_schema import ProductionDetailInput, ProductionPeriodCreate


class ProductionService:
    def __init__(self, db: Session, contract_client: ContractClient) -> None:
        self.db = db
        self.contract_client = contract_client

    def check_overlap(self, customer_id: str, contract_id: str, from_date, to_date) -> list[int]:
        return [period.id for period in production_crud.find_overlapping_periods(self.db, customer_id, contract_id, from_date, to_date)]

    def create_draft(self, payload: ProductionPeriodCreate, actor_id: str) -> ProductionPeriod:
        contract = self._validate_contract(payload.contract_id, payload.from_date, payload.to_date, payload.customer_id)
        self._validate_details(payload.details, payload.from_date, payload.to_date, contract.allowed_service_codes)
        conflicts = self.check_overlap(payload.customer_id, payload.contract_id, payload.from_date, payload.to_date)
        if conflicts:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A production period overlaps the requested dates")
        period = ProductionPeriod(
            customer_id=payload.customer_id,
            contract_id=payload.contract_id,
            period_name=self._next_period_code(payload.contract_id),
            from_date=payload.from_date,
            to_date=payload.to_date,
            status=ProductionPeriodStatus.DRAFT.value,
            details=[self._detail_model(detail) for detail in payload.details],
        )
        try:
            production_crud.create_period(self.db, period)
            record_event(self.db, "PRODUCTION_PERIOD_DRAFT_CREATED", period.id, self._event_payload(period, actor_id, None, "DRAFT"))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return production_crud.get_period(self.db, period.id)  # type: ignore[return-value]

    def get_period(self, period_id: int) -> ProductionPeriod:
        period = production_crud.get_period(self.db, period_id)
        if period is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Production period not found")
        return period

    def list_periods(self, customer_id: str | None, contract_id: str | None) -> list[ProductionPeriod]:
        return production_crud.list_periods(self.db, customer_id, contract_id)

    def replace_details(self, period_id: int, details: list[ProductionDetailInput]) -> ProductionPeriod:
        period = self.get_period(period_id)
        self._require_editable(period)
        contract = self._validate_contract(period.contract_id, period.from_date, period.to_date, period.customer_id)
        self._validate_details(details, period.from_date, period.to_date, contract.allowed_service_codes)
        try:
            production_crud.replace_details(period, [self._detail_model(detail) for detail in details])
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return self.get_period(period_id)

    def lock_period(self, period_id: int, actor_id: str) -> ProductionPeriod:
        period = self.get_period(period_id)
        if period.status == ProductionPeriodStatus.LOCKED.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Production period is already locked")
        if not period.details:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="A production period needs at least one detail before locking")
        contract = self._validate_contract(period.contract_id, period.from_date, period.to_date, period.customer_id)
        self._validate_details([self._detail_input(detail) for detail in period.details], period.from_date, period.to_date, contract.allowed_service_codes)
        previous_status = period.status
        period.status = ProductionPeriodStatus.LOCKED.value
        period.locked_at = datetime.now(timezone.utc)
        period.locked_by = actor_id
        try:
            record_event(self.db, "PRODUCTION_PERIOD_LOCKED", period.id, self._event_payload(period, actor_id, previous_status, period.status))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return self.get_period(period_id)

    @staticmethod
    def totals(period: ProductionPeriod) -> list[dict]:
        grouped: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
        for detail in period.details:
            grouped[(detail.service_code, detail.unit)] += detail.quantity
        return [
            {"service_code": service_code, "unit": unit, "quantity": quantity}
            for (service_code, unit), quantity in sorted(grouped.items())
        ]

    def _validate_contract(self, contract_id, from_date, to_date, customer_id):
        try:
            contract = self.contract_client.validate_production_period(contract_id, from_date, to_date)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
        if contract.customer_id != customer_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Customer does not match the contract")
        return contract

    def _next_period_code(self, contract_id: str) -> str:
        match = re.search(r"20\d{2}", contract_id)
        if match is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Contract ID must contain a four-digit year, for example HD-2024-TCB-082",
            )
        year = match.group(0)
        sequence = sum(
            1
            for existing_contract_id in production_crud.list_contract_ids(self.db)
            if re.search(r"20\d{2}", existing_contract_id)
            and re.search(r"20\d{2}", existing_contract_id).group(0) == year
        ) + 1
        return f"SL-{year}-{sequence:03d}"

    @staticmethod
    def _validate_details(details, from_date, to_date, allowed_service_codes: set[str]) -> None:
        seen: set[tuple[str, object]] = set()
        for detail in details:
            if detail.recorded_date < from_date or detail.recorded_date > to_date:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Each recorded_date must fall within the production period")
            if detail.service_code not in allowed_service_codes:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"Service '{detail.service_code}' is not on the contract")
            key = (detail.service_code, detail.recorded_date)
            if key in seen:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="A service may be recorded only once per day in a period")
            seen.add(key)

    @staticmethod
    def _detail_model(detail: ProductionDetailInput) -> ProductionDetail:
        return ProductionDetail(**detail.model_dump())

    @staticmethod
    def _detail_input(detail: ProductionDetail) -> ProductionDetailInput:
        return ProductionDetailInput(service_code=detail.service_code, recorded_date=detail.recorded_date, quantity=detail.quantity, unit=detail.unit, notes=detail.notes)

    @staticmethod
    def _require_editable(period: ProductionPeriod) -> None:
        if period.status != ProductionPeriodStatus.DRAFT.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Locked production data cannot be changed directly")

    @staticmethod
    def _event_payload(period: ProductionPeriod, actor_id: str, status_before: str | None, status_after: str) -> dict:
        return {
            "actor_id": actor_id,
            "period_id": period.id,
            "customer_id": period.customer_id,
            "contract_id": period.contract_id,
            "status_before": status_before,
            "status_after": status_after,
            "recipient_role": "ROLE_ACCOUNTANT" if status_after == ProductionPeriodStatus.LOCKED.value else None,
        }
