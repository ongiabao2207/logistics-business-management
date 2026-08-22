from sqlalchemy.orm import Session

from app.clients.price_client import ServicePriceInfo
from app.models.contract_model import Contract, ContractService as ContractServiceModel
from app.schemas.contract_schema import ContractCreate


class ContractCRUD:
    def create(
        self,
        db: Session,
        contract_in: ContractCreate,
        service_prices: list[ServicePriceInfo],
    ) -> Contract:
        contract = Contract(
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
            )
            for service_price in service_prices
        ]

        db.add(contract)
        db.commit()
        db.refresh(contract)
        return contract


contract_crud = ContractCRUD()
