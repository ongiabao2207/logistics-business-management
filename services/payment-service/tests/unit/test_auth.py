import pytest
from fastapi import HTTPException

from app.core.auth import CurrentUser, get_current_user, require_roles


def user(role: str) -> CurrentUser:
    return CurrentUser(
        account_id="user-1",
        username="test_user",
        role=role,
        access_token="test-token",
    )


def test_missing_bearer_token_returns_401():
    with pytest.raises(HTTPException) as error:
        get_current_user(None)

    assert error.value.status_code == 401
    assert error.value.detail == "Bearer token is required"


def test_allowed_role_is_accepted():
    result = require_roles("ROLE_SALE")(user("ROLE_SALE"))
    assert result.role == "ROLE_SALE"


def test_disallowed_role_returns_403():
    with pytest.raises(HTTPException) as error:
        require_roles("ROLE_ADMIN")(user("ROLE_SALE"))

    assert error.value.status_code == 403
    assert error.value.detail == "Insufficient role"
