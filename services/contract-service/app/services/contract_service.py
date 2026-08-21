from sqlalchemy.orm import Session

from app.clients.customer_client import CustomerClient
from app.crud.contract_crud import ContractCRUD, contract_crud
from app.models.contract_model import Contract
from app.schemas.contract_schema import ContractCreate


class ContractValidationError(ValueError):
    pass


class CustomerNotFoundError(ContractValidationError):
    pass


class CustomerInactiveError(ContractValidationError):
    pass


class ContractService:
    def __init__(
        self,
        customer_client: CustomerClient,
        crud: ContractCRUD = contract_crud,
    ) -> None:
        self.customer_client = customer_client
        self.crud = crud

    def create_contract(self, db: Session, contract_in: ContractCreate) -> Contract:
        self._validate_effective_period(contract_in)
        self._validate_customer(contract_in.customer_id)
        return self.crud.create(db, contract_in)

    def _validate_effective_period(self, contract_in: ContractCreate) -> None:
        if contract_in.valid_from > contract_in.valid_to:
            raise ContractValidationError("valid_from must not be later than valid_to")

    def _validate_customer(self, customer_id: str) -> None:
        customer = self.customer_client.get_customer(customer_id)

        if customer is None:
            raise CustomerNotFoundError("customer does not exist")

        if not customer.active:
            raise CustomerInactiveError("customer is inactive")
