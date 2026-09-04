from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.clients.customer_client import get_customer_client
from app.clients.price_client import get_price_client
from app.core.auth import CurrentUser, get_current_user, require_roles
from app.core.config import get_settings
from app.db.session import get_db
from app.messaging.producer import RabbitMQEventPublisher
from app.schemas.contract_schema import (
    ContractCreate,
    ContractDetailRead,
    ContractRead,
    ContractSummaryRead,
    ProductionContractValidationRead,
    ContractStatusUpdate,
    ContractUpdate,
)
from app.services.contract_service import (
    ContractNotDeletableError,
    ContractNotEditableError,
    ContractNotFoundError,
    ContractNumberLimitError,
    ContractService,
    ContractValidationError,
    CustomerInactiveError,
    CustomerNotFoundError,
    CustomerServiceDependencyError,
    IdempotencyConflictError,
    InvalidContractStatusTransitionError,
    PriceServiceDependencyError,
)

router = APIRouter(prefix="/contracts", tags=["contracts"])


def get_contract_service(
    current_user: CurrentUser = Depends(get_current_user),
) -> ContractService:
    settings = get_settings()
    return ContractService(
        customer_client=get_customer_client(current_user.access_token),
        price_client=get_price_client(current_user.access_token),
        events=RabbitMQEventPublisher(settings.rabbitmq_url, settings.rabbitmq_enabled),
    )


@router.get("", response_model=list[ContractSummaryRead])
def list_contracts(
    _current_user: Annotated[CurrentUser, Depends(require_roles("ROLE_SALE", "ROLE_LEGAL", "ROLE_DIRECTOR", "ROLE_ACCOUNTANT", "ROLE_OPERATION"))],
    db: Session = Depends(get_db),
    service: ContractService = Depends(get_contract_service),
):
    try:
        return service.list_contracts(db)
    except CustomerServiceDependencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )


@router.post(
    "",
    response_model=ContractRead,
    status_code=status.HTTP_201_CREATED,
)
def create_contract(
    contract_in: ContractCreate,
    _current_user: Annotated[CurrentUser, Depends(require_roles("ROLE_SALE"))],
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
    except CustomerServiceDependencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )
    except IdempotencyConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ContractNumberLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except PriceServiceDependencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )
    except ContractValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )


@router.patch("/{contract_id}/status", response_model=ContractDetailRead)
def update_contract_status(
    contract_id: str,
    status_in: ContractStatusUpdate,
    _current_user: Annotated[CurrentUser, Depends(require_roles("ROLE_SALE"))],
    db: Session = Depends(get_db),
    service: ContractService = Depends(get_contract_service),
):
    try:
        return service.update_contract_status(db, contract_id, status_in)
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidContractStatusTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )


@router.patch("/{contract_id}", response_model=ContractDetailRead)
def update_contract(
    contract_id: str,
    contract_in: ContractUpdate,
    _current_user: Annotated[CurrentUser, Depends(require_roles("ROLE_SALE"))],
    db: Session = Depends(get_db),
    service: ContractService = Depends(get_contract_service),
):
    try:
        return service.update_contract(db, contract_id, contract_in)
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ContractNotEditableError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except PriceServiceDependencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )
    except ContractValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )


@router.get("/{contract_id}", response_model=ContractDetailRead)
def get_contract_detail(
    contract_id: str,
    _current_user: Annotated[CurrentUser, Depends(require_roles("ROLE_SALE", "ROLE_LEGAL", "ROLE_DIRECTOR", "ROLE_ACCOUNTANT", "ROLE_OPERATION"))],
    db: Session = Depends(get_db),
    service: ContractService = Depends(get_contract_service),
):
    try:
        return service.get_contract_detail(db, contract_id)
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except CustomerServiceDependencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )
    except ContractValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )


@router.get("/{contract_id}/validate-services", response_model=ProductionContractValidationRead)
def validate_production_period(
    contract_id: str,
    fromDate: date,
    toDate: date,
    _current_user: Annotated[CurrentUser, Depends(require_roles("ROLE_OPERATION"))],
    db: Session = Depends(get_db),
    service: ContractService = Depends(get_contract_service),
):
    try:
        return service.validate_production_period(db, contract_id, fromDate, toDate)
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ContractValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(
    contract_id: str,
    _current_user: Annotated[CurrentUser, Depends(require_roles("ROLE_SALE"))],
    db: Session = Depends(get_db),
    service: ContractService = Depends(get_contract_service),
):
    try:
        service.delete_contract(db, contract_id)
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ContractNotDeletableError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
