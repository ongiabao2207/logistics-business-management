from sqlalchemy.orm import Session

from app.models.contract_model import Contract
from app.schemas.contract_schema import ContractCreate


class ContractCRUD:
    def create(self, db: Session, contract_in: ContractCreate) -> Contract:
        contract = Contract(
            customer_id=contract_in.customer_id,
            valid_from=contract_in.valid_from,
            valid_to=contract_in.valid_to,
            payment_terms=contract_in.payment_terms,
            status="DRAFT",
        )
        db.add(contract)
        db.commit()
        db.refresh(contract)
        return contract


contract_crud = ContractCRUD()
