from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.routers.dependencies import require_admin
from app.schemas.identity_schema import CurrentUser, RoleResponse
from app.services.identity_service import IdentityService


router = APIRouter(prefix="/api/v1/roles", tags=["roles"])


@router.get("", response_model=list[RoleResponse])
def list_roles(
    _admin: Annotated[CurrentUser, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> list[RoleResponse]:
    return IdentityService().crud.list_roles(db)
