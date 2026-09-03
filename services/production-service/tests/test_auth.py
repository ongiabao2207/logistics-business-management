import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.auth import CurrentUser, get_current_user, require_roles
from app.routers.production_router import get_production_service, router


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


class ProductionReadStub:
    def list_periods(self, customer_id: str | None, contract_id: str | None) -> list:
        return []

    def get_period(self, period_id: int) -> dict:
        return {
            "id": period_id,
            "customer_id": "customer-1",
            "contract_id": "contract-1",
            "period_name": "October 2026",
            "from_date": "2026-10-01",
            "to_date": "2026-10-31",
            "status": "LOCKED",
            "locked_at": "2026-11-01T00:00:00",
            "locked_by": "operation-1",
            "created_at": "2026-10-01T00:00:00",
            "updated_at": "2026-11-01T00:00:00",
            "details": [],
        }

    def totals(self, _period: dict) -> list:
        return []


@pytest.fixture
def accountant_client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: user("ROLE_ACCOUNTANT")
    app.dependency_overrides[get_production_service] = ProductionReadStub
    return TestClient(app)


def test_accountant_can_list_production_periods(accountant_client: TestClient):
    response = accountant_client.get("/api/v1/production-periods")

    assert response.status_code == 200
    assert response.json() == []


def test_accountant_can_view_production_period_detail(accountant_client: TestClient):
    response = accountant_client.get("/api/v1/production-periods/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
