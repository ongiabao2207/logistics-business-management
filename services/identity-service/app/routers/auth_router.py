from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.routers.dependencies import get_current_user, get_identity_service
from app.schemas.identity_schema import AccountResponse, CurrentUser, LoginRequest, TokenResponse
from app.services.identity_service import IdentityService


router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> TokenResponse:
    return service.authenticate(db, payload.username, payload.password, settings)


@router.get("/me", response_model=AccountResponse)
def me(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> AccountResponse:
    return service.require_account(db, current_user.id)
