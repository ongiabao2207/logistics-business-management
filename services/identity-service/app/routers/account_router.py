from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.routers.dependencies import get_identity_service, require_admin
from app.schemas.identity_schema import (
    AccountCreate,
    AccountResponse,
    AccountRoleUpdate,
    AccountStatusUpdate,
    AccountUpdate,
    CurrentUser,
)
from app.services.identity_service import IdentityService


router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    _admin: Annotated[CurrentUser, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> AccountResponse:
    return service.create_account(db, payload)


@router.get("", response_model=list[AccountResponse])
def list_accounts(
    _admin: Annotated[CurrentUser, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> list[AccountResponse]:
    return service.crud.list_accounts(db)


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    _admin: Annotated[CurrentUser, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> AccountResponse:
    return service.require_account(db, account_id)


@router.patch("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    payload: AccountUpdate,
    _admin: Annotated[CurrentUser, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> AccountResponse:
    return service.update_account(db, account_id, payload)


@router.patch("/{account_id}/status", response_model=AccountResponse)
def update_account_status(
    account_id: int,
    payload: AccountStatusUpdate,
    admin: Annotated[CurrentUser, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> AccountResponse:
    return service.update_status(db, account_id, payload.is_active, admin.id)


@router.put("/{account_id}/role", response_model=AccountResponse)
def update_account_role(
    account_id: int,
    payload: AccountRoleUpdate,
    _admin: Annotated[CurrentUser, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> AccountResponse:
    return service.update_role(db, account_id, payload.role_id)
