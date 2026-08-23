from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.clients.customer_client import CustomerClient, get_customer_client
from app.clients.price_client import PriceClient, get_price_client
from app.db.session import get_db
from app.schemas.contract_schema import (
    ContractCreate,
    ContractDetailRead,
    ContractRead,
    ContractSummaryRead,
)
from app.services.contract_service import (
    ContractNumberLimitError,
    ContractNotFoundError,
    ContractService,
    ContractValidationError,
    CustomerInactiveError,
    CustomerNotFoundError,
    IdempotencyConflictError,
)

router = APIRouter(prefix="/contracts", tags=["contracts"])


def get_contract_service(
    customer_client: CustomerClient = Depends(get_customer_client),
    price_client: PriceClient = Depends(get_price_client),
) -> ContractService:
    return ContractService(customer_client=customer_client, price_client=price_client)


@router.get("", response_model=list[ContractSummaryRead])
def list_contracts(
    db: Session = Depends(get_db),
    service: ContractService = Depends(get_contract_service),
):
    return service.list_contracts(db)


@router.post(
    "",
    response_model=ContractRead,
    status_code=status.HTTP_201_CREATED,
)
def create_contract(
    contract_in: ContractCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    service: ContractService = Depends(get_contract_service),
):
    if idempotency_key is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required",
        )

    try:
        return service.create_contract(db, contract_in, idempotency_key)
    except CustomerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except CustomerInactiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except IdempotencyConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ContractNumberLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except ContractValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )


@router.get("/{contract_id}", response_model=ContractDetailRead)
def get_contract_detail(
    contract_id: str,
    db: Session = Depends(get_db),
    service: ContractService = Depends(get_contract_service),
):
    try:
        return service.get_contract_detail(db, contract_id)
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ContractValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
