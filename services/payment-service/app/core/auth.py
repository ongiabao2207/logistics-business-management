from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.core.config import get_settings


@dataclass(frozen=True)
class CurrentUser:
    account_id: str
    username: str | None
    role: str
    access_token: str


bearer = HTTPBearer(auto_error=False)


@lru_cache
def get_jwks_client() -> PyJWKClient:
    return PyJWKClient(get_settings().identity_jwks_url, cache_keys=True)


def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token is required")
    settings = get_settings()
    try:
        key = get_jwks_client().get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(
            credentials.credentials,
            key.key,
            algorithms=["RS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "role", "iss", "aud", "iat", "exp", "jti"]},
        )
        return CurrentUser(str(claims["sub"]), claims.get("username"), claims["role"], credentials.credentials)
    except (jwt.PyJWTError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token") from exc


def require_roles(*allowed_roles: str) -> Callable:
    def dependency(current_user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return current_user

    return dependency
