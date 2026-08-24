from collections.abc import Callable
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from app.clients.price_client import ServicePriceInfo
from app.models.contract_model import (
    Contract,
    ContractService as ContractServiceModel,
    ContractYearSequence,
    IdempotencyRecord,
    utc_now,
)
from app.schemas.contract_schema import (
    ContractCreate,
    ContractServiceCreate,
    ContractUpdate,
)


class ContractNumberLimitReachedError(ValueError):
    pass


class ContractCRUD:
    def __init__(self, current_year: Callable[[], int] | None = None) -> None:
        self.current_year = current_year or (lambda: date.today().year)

    def create(
        self,
        db: Session,
        contract_in: ContractCreate,
        service_prices: list[tuple[ContractServiceCreate, ServicePriceInfo]],
        idempotency_key: str,
        request_hash: str,
    ) -> Contract:
        contract_id = self._next_contract_id(db)
        contract = Contract(
            id=contract_id,
            customer_id=contract_in.customer_id,
            valid_from=contract_in.valid_from,
            valid_to=contract_in.valid_to,
            payment_terms=contract_in.payment_terms,
            status="DRAFT",
        )
        contract.services = [
            ContractServiceModel(
                service_id=service_price.service_id,
                service_name=service_price.service_name,
                service_unit=service_price.service_unit,
                service_price=service_price.service_price,
                quantity=service_in.quantity,
            )
            for service_in, service_price in service_prices
        ]

        db.add(contract)
        db.add(
            IdempotencyRecord(
                endpoint="POST /contracts",
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                resource_type="contract",
                resource_id=contract_id,
            )
        )
        db.commit()
        db.refresh(contract)
        return contract

    def get_idempotency_record(
        self, db: Session, endpoint: str, idempotency_key: str
    ) -> IdempotencyRecord | None:
        statement = select(IdempotencyRecord).where(
            IdempotencyRecord.endpoint == endpoint,
            IdempotencyRecord.idempotency_key == idempotency_key,
        )
        return db.scalar(statement)

    def list_all(self, db: Session) -> list[Contract]:
        statement = select(Contract).options(selectinload(Contract.services))
        return list(db.scalars(statement).all())

    def get_by_id(self, db: Session, contract_id: str) -> Contract | None:
        statement = (
            select(Contract)
            .where(Contract.id == contract_id)
            .options(selectinload(Contract.services))
        )
        return db.scalar(statement)

    def update_status(self, db: Session, contract: Contract, status: str) -> Contract:
        contract.status = status
        contract.updated_at = utc_now()
        db.add(contract)
        db.commit()
        db.refresh(contract)
        return contract

    def update_contract(
        self,
        db: Session,
        contract: Contract,
        contract_in: ContractUpdate,
        service_prices: list[tuple[ContractServiceCreate, ServicePriceInfo]] | None,
    ) -> Contract:
        if contract_in.valid_from is not None:
            contract.valid_from = contract_in.valid_from

        if contract_in.valid_to is not None:
            contract.valid_to = contract_in.valid_to

        if contract_in.payment_terms is not None:
            contract.payment_terms = contract_in.payment_terms

        if service_prices is not None:
            contract.services = [
                ContractServiceModel(
                    service_id=service_price.service_id,
                    service_name=service_price.service_name,
                    service_unit=service_price.service_unit,
                    service_price=service_price.service_price,
                    quantity=service_in.quantity,
                )
                for service_in, service_price in service_prices
            ]

        contract.updated_at = utc_now()
        db.add(contract)
        db.commit()
        db.refresh(contract)
        return contract

    def delete(self, db: Session, contract: Contract) -> None:
        db.delete(contract)
        db.commit()

    def _next_contract_id(self, db: Session) -> str:
        year = self.current_year()
        self._lock_contract_year(db, year)
        sequence = self._get_or_create_year_sequence(db, year)

        if sequence.last_number >= 999:
            raise ContractNumberLimitReachedError(
                f"contract number limit reached for year {year}"
            )

        sequence.last_number += 1
        db.add(sequence)
        return f"HD-{year}-{sequence.last_number:03d}"

    def _lock_contract_year(self, db: Session, year: int) -> None:
        if db.bind is not None and db.bind.dialect.name == "postgresql":
            db.execute(
                text("SELECT pg_advisory_xact_lock(:lock_key)"),
                {"lock_key": year},
            )

    def _get_or_create_year_sequence(
        self, db: Session, year: int
    ) -> ContractYearSequence:
        statement = (
            select(ContractYearSequence)
            .where(ContractYearSequence.year == year)
            .with_for_update()
        )
        sequence = db.scalar(statement)
        if sequence is not None:
            return sequence

        sequence = ContractYearSequence(year=year, last_number=0)
        db.add(sequence)
        db.flush()
        return sequence


contract_crud = ContractCRUD()
