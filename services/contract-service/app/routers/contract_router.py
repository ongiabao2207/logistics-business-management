from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.clients.customer_client import CustomerClient, get_customer_client
from app.clients.price_client import PriceClient, get_price_client
from app.db.session import get_db
from app.schemas.contract_schema import ContractCreate, ContractRead
from app.services.contract_service import (
    ContractService,
    ContractValidationError,
    CustomerInactiveError,
    CustomerNotFoundError,
)

router = APIRouter(prefix="/contracts", tags=["contracts"])


def get_contract_service(
    customer_client: CustomerClient = Depends(get_customer_client),
    price_client: PriceClient = Depends(get_price_client),
) -> ContractService:
    return ContractService(customer_client=customer_client, price_client=price_client)


@router.post(
    "",
    response_model=ContractRead,
    status_code=status.HTTP_201_CREATED,
)
def create_contract(
    contract_in: ContractCreate,
    db: Session = Depends(get_db),
    service: ContractService = Depends(get_contract_service),
):
    try:
        return service.create_contract(db, contract_in)
    except CustomerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except CustomerInactiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except ContractValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
