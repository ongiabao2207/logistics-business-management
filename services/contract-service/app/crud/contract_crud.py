from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.clients.price_client import ServicePriceInfo
from app.models.contract_model import Contract, ContractService as ContractServiceModel
from app.schemas.contract_schema import ContractCreate, ContractServiceCreate, ContractUpdate


class ContractCRUD:
    def create(
        self,
        db: Session,
        contract_in: ContractCreate,
        service_prices: list[tuple[ContractServiceCreate, ServicePriceInfo]],
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
                quantity=service_in.quantity,
            )
            for service_in, service_price in service_prices
        ]

        db.add(contract)
        db.commit()
        db.refresh(contract)
        return contract

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

        db.add(contract)
        db.commit()
        db.refresh(contract)
        return contract

    def delete(self, db: Session, contract: Contract) -> None:
        db.delete(contract)
        db.commit()


contract_crud = ContractCRUD()
