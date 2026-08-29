import hashlib
import json
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.clients.customer_client import CustomerClient
from app.clients.price_client import PriceClient, PriceClientError, ServicePriceInfo
from app.crud.contract_crud import (
    ContractCRUD,
    ContractNumberLimitReachedError,
    contract_crud,
)
from app.models.contract_model import Contract
from app.schemas.contract_schema import (
    ContractCreate,
    ContractDetailRead,
    ContractDetailServiceRead,
    ContractServiceCreate,
    ContractSummaryRead,
    ContractStatusUpdate,
    ContractUpdate,
)


class ContractValidationError(ValueError):
    pass


class CustomerNotFoundError(ContractValidationError):
    pass


class CustomerInactiveError(ContractValidationError):
    pass


class DuplicateContractServiceError(ContractValidationError):
    pass


class ContractServiceUnavailableError(ContractValidationError):
    pass


class PriceServiceDependencyError(ContractValidationError):
    pass


class ContractNotFoundError(ContractValidationError):
    pass


class IdempotencyConflictError(ContractValidationError):
    pass


class ContractNumberLimitError(ContractValidationError):
    pass


class InvalidContractStatusTransitionError(ContractValidationError):
    pass


class ContractNotEditableError(ContractValidationError):
    pass


class ContractNotDeletableError(ContractValidationError):
    pass


class ContractService:
    _create_contract_endpoint = "POST /api/v1/contracts"
    _allowed_status_transitions = {
        "DRAFT": {"SUBMITTED"},
        "SUBMITTED": {"ACTIVE"},
        "ACTIVE": {"EXPIRED"},
        "EXPIRED": set(),
    }

    def __init__(
        self,
        customer_client: CustomerClient,
        price_client: PriceClient,
        crud: ContractCRUD = contract_crud,
    ) -> None:
        self.customer_client = customer_client
        self.price_client = price_client
        self.crud = crud

    def create_contract(
        self, db: Session, contract_in: ContractCreate, idempotency_key: str
    ) -> Contract:
        request_hash = self._hash_create_request(contract_in)
        existing_record = self.crud.get_idempotency_record(
            db, self._create_contract_endpoint, idempotency_key
        )
        if existing_record is not None:
            if existing_record.request_hash != request_hash:
                raise IdempotencyConflictError(
                    "idempotency key was already used with a different request"
                )

            existing_contract = self.crud.get_by_id(db, existing_record.resource_id)
            if existing_contract is None:
                raise ContractValidationError(
                    "idempotency record points to a missing contract"
                )
            return existing_contract

        self._validate_effective_period(contract_in)
        self._validate_customer(contract_in.customer_id)
        service_prices = self._resolve_service_prices(contract_in.services)
        try:
            return self.crud.create(
                db,
                contract_in,
                service_prices,
                self._create_contract_endpoint,
                idempotency_key,
                request_hash,
            )
        except ContractNumberLimitReachedError as exc:
            raise ContractNumberLimitError(str(exc)) from exc

    def list_contracts(self, db: Session) -> list[ContractSummaryRead]:
        contracts = self.crud.list_all(db)
        return [self._to_summary(contract) for contract in contracts]

    def get_contract_detail(self, db: Session, contract_id: str) -> ContractDetailRead:
        contract = self._get_contract_or_raise(db, contract_id)
        return self._to_detail(contract)

    def update_contract_status(
        self,
        db: Session,
        contract_id: str,
        status_in: ContractStatusUpdate,
    ) -> ContractDetailRead:
        contract = self._get_contract_or_raise(db, contract_id)
        self._validate_status_transition(contract.status, status_in.status)
        updated_contract = self.crud.update_status(db, contract, status_in.status)
        return self._to_detail(updated_contract)

    def update_contract(
        self,
        db: Session,
        contract_id: str,
        contract_in: ContractUpdate,
    ) -> ContractDetailRead:
        contract = self._get_contract_or_raise(db, contract_id)
        if contract.status != "DRAFT":
            raise ContractNotEditableError("only DRAFT contracts can be modified")

        valid_from = contract_in.valid_from or contract.valid_from
        valid_to = contract_in.valid_to or contract.valid_to
        self._validate_update_effective_dates(valid_from, valid_to)

        service_prices = None
        if contract_in.services is not None:
            service_prices = self._resolve_service_prices(contract_in.services)

        updated_contract = self.crud.update_contract(
            db,
            contract,
            contract_in,
            service_prices,
        )
        return self._to_detail(updated_contract)

    def delete_contract(self, db: Session, contract_id: str) -> None:
        contract = self._get_contract_or_raise(db, contract_id)
        if contract.status != "DRAFT":
            raise ContractNotDeletableError("only DRAFT contracts can be deleted")

        self.crud.delete(db, contract)

    def _validate_effective_period(self, contract_in: ContractCreate) -> None:
        self._validate_effective_dates(contract_in.valid_from, contract_in.valid_to)

    def _validate_effective_dates(self, valid_from: date, valid_to: date) -> None:
        if valid_from > valid_to:
            raise ContractValidationError("valid_from must not be later than valid_to")

    def _validate_update_effective_dates(
        self, valid_from: date, valid_to: date
    ) -> None:
        if valid_from <= date.today():
            raise ContractValidationError("valid_from must be greater than current date")

        if valid_to <= valid_from:
            raise ContractValidationError("valid_to must be greater than valid_from")

    def _hash_create_request(self, contract_in: ContractCreate) -> str:
        payload = contract_in.model_dump(mode="json")
        canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()

    def _validate_customer(self, customer_id: str) -> None:
        customer = self.customer_client.get_customer(customer_id)

        if customer is None:
            raise CustomerNotFoundError("customer does not exist")

        if customer.status != "ACTIVE":
            raise CustomerInactiveError("customer is not active")

    def _resolve_service_prices(
        self, services: list[ContractServiceCreate]
    ) -> list[tuple[ContractServiceCreate, ServicePriceInfo]]:
        service_ids = [service.service_id for service in services]
        duplicate_service_ids = {
            service_id for service_id in service_ids if service_ids.count(service_id) > 1
        }
        if duplicate_service_ids:
            formatted_ids = ", ".join(
                str(service_id) for service_id in sorted(duplicate_service_ids)
            )
            raise DuplicateContractServiceError(
                f"duplicate service_id values are not allowed: {formatted_ids}"
            )

        service_prices: list[tuple[ContractServiceCreate, ServicePriceInfo]] = []
        missing_service_ids: list[int] = []

        for service in services:
            try:
                service_price = self.price_client.get_service_price(service.service_id)
            except PriceClientError as exc:
                raise PriceServiceDependencyError("price service is unavailable") from exc
            if service_price is None:
                missing_service_ids.append(service.service_id)
                continue
            service_prices.append((service, service_price))

        if missing_service_ids:
            formatted_ids = ", ".join(
                str(service_id) for service_id in missing_service_ids
            )
            raise ContractServiceUnavailableError(
                f"service_id values are not available: {formatted_ids}"
            )

        return service_prices

    def _get_contract_or_raise(self, db: Session, contract_id: str) -> Contract:
        contract = self.crud.get_by_id(db, contract_id)
        if contract is None:
            raise ContractNotFoundError("contract does not exist")
        return contract

    def _validate_status_transition(self, current_status: str, target_status: str) -> None:
        allowed_statuses = self._allowed_status_transitions.get(current_status, set())
        if target_status not in allowed_statuses:
            raise InvalidContractStatusTransitionError(
                f"cannot transition contract from {current_status} to {target_status}"
            )

    def _to_summary(self, contract: Contract) -> ContractSummaryRead:
        return ContractSummaryRead(
            contract_id=contract.id,
            customer_name=self._resolve_customer_name(contract.customer_id),
            valid_from=contract.valid_from,
            valid_to=contract.valid_to,
            total_value=sum(
                (
                    service.quantity * service.service_price
                    for service in contract.services
                ),
                Decimal("0.00"),
            ),
            status=contract.status,
        )

    def _resolve_customer_name(self, customer_id: str) -> str:
        customer = self.customer_client.get_customer(customer_id)
        if customer is None:
            return "Unknown Customer"
        return customer.name

    def _to_detail(self, contract: Contract) -> ContractDetailRead:
        summary = self._to_summary(contract)
        return ContractDetailRead(
            **summary.model_dump(),
            payment_terms=contract.payment_terms,
            updated_at=contract.updated_at,
            services=[
                ContractDetailServiceRead(
                    id=service.id,
                    service_name=service.service_name,
                    service_unit=service.service_unit,
                    service_price=service.service_price,
                    quantity=service.quantity,
                )
                for service in contract.services
            ],
        )
