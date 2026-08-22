from sqlalchemy.orm import Session

from app.clients.customer_client import CustomerClient
from app.clients.price_client import PriceClient, ServicePriceInfo
from app.crud.contract_crud import ContractCRUD, contract_crud
from app.models.contract_model import Contract
from app.schemas.contract_schema import ContractCreate


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
