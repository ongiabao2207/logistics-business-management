from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import TokenValidationError, decode_access_token
from app.db.session import get_db
from app.schemas.identity_schema import CurrentUser
from app.services.identity_service import IdentityService


bearer = HTTPBearer(auto_error=False)


def get_identity_service() -> IdentityService:
    return IdentityService()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
    service: Annotated[IdentityService, Depends(get_identity_service)],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token is required")
    try:
        claims = decode_access_token(credentials.credentials, settings)
        account_id = int(claims["sub"])
    except (TokenValidationError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token") from exc
    account = service.require_account(db, account_id)
    if not account.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    return CurrentUser(id=account.id, username=account.username, role=account.role.name)


def require_admin(current_user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    if current_user.role != "ROLE_ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ROLE_ADMIN is required")
    return current_user
