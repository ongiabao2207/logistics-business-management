from decimal import Decimal

from sqlalchemy.orm import Session

from app.clients.customer_client import CustomerClient
from app.clients.price_client import PriceClient, ServicePriceInfo
from app.crud.contract_crud import ContractCRUD, contract_crud
from app.models.contract_model import Contract
from app.schemas.contract_schema import (
    ContractCreate,
    ContractDetailRead,
    ContractDetailServiceRead,
    ContractSummaryRead,
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


class ContractNotFoundError(ContractValidationError):
    pass


class ContractService:
    def __init__(
        self,
        customer_client: CustomerClient,
        price_client: PriceClient,
        crud: ContractCRUD = contract_crud,
    ) -> None:
        self.customer_client = customer_client
        self.price_client = price_client
        self.crud = crud

    def create_contract(self, db: Session, contract_in: ContractCreate) -> Contract:
        self._validate_effective_period(contract_in)
        self._validate_customer(contract_in.customer_id)
        service_prices = self._resolve_service_prices(contract_in.service_ids)
        return self.crud.create(db, contract_in, service_prices)

    def list_contracts(self, db: Session) -> list[ContractSummaryRead]:
        contracts = self.crud.list_all(db)
        return [self._to_summary(contract) for contract in contracts]

    def get_contract_detail(self, db: Session, contract_id: str) -> ContractDetailRead:
        contract = self.crud.get_by_id(db, contract_id)
        if contract is None:
            raise ContractNotFoundError("contract does not exist")

        summary = self._to_summary(contract)
        return ContractDetailRead(
            **summary.model_dump(),
            updated_at=contract.updated_at,
            services=[
                ContractDetailServiceRead(
                    id=service.id,
                    service_name=service.service_name,
                    service_unit=service.service_unit,
                    service_price=service.service_price,
                )
                for service in contract.services
            ],
        )

    def _validate_effective_period(self, contract_in: ContractCreate) -> None:
        if contract_in.valid_from > contract_in.valid_to:
            raise ContractValidationError("valid_from must not be later than valid_to")

    def _validate_customer(self, customer_id: str) -> None:
        customer = self.customer_client.get_customer(customer_id)

        if customer is None:
            raise CustomerNotFoundError("customer does not exist")

        if not customer.active:
            raise CustomerInactiveError("customer is inactive")

    def _resolve_service_prices(self, service_ids: list[int]) -> list[ServicePriceInfo]:
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

        service_prices: list[ServicePriceInfo] = []
        missing_service_ids: list[int] = []

        for service_id in service_ids:
            service_price = self.price_client.get_service_price(service_id)
            if service_price is None:
                missing_service_ids.append(service_id)
                continue
            service_prices.append(service_price)

        if missing_service_ids:
            formatted_ids = ", ".join(
                str(service_id) for service_id in missing_service_ids
            )
            raise ContractServiceUnavailableError(
                f"service_id values are not available: {formatted_ids}"
            )

        return service_prices

    def _to_summary(self, contract: Contract) -> ContractSummaryRead:
        return ContractSummaryRead(
            contract_id=contract.id,
            customer_name=self._resolve_customer_name(contract.customer_id),
            valid_from=contract.valid_from,
            valid_to=contract.valid_to,
            total_value=sum(
                (service.service_price for service in contract.services),
                Decimal("0.00"),
            ),
            status=contract.status,
        )

    def _resolve_customer_name(self, customer_id: str) -> str:
        customer = self.customer_client.get_customer(customer_id)
        if customer is None:
            return "Unknown Customer"
        return customer.name
