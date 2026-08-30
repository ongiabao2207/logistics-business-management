from datetime import date, timedelta
from decimal import Decimal

import pytest

pytest.importorskip("httpx")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.clients.customer_client import CustomerInfo
from app.clients.price_client import ServicePriceInfo
from app.db.base import Base
from app.db.session import get_db
from app.core.auth import CurrentUser, get_current_user
from app.routers.contract_router import get_contract_service, router
from app.services.contract_service import ContractService


API_PREFIX = "/api/v1"


class StubCustomerClient:
    def __init__(self, customer: CustomerInfo | None) -> None:
        self.customer = customer

    def get_customer(self, customer_id: str) -> CustomerInfo | None:
        return self.customer


class StubPriceClient:
    def get_service_price(self, service_id: int) -> ServicePriceInfo | None:
        if service_id == 1:
            return ServicePriceInfo(
                service_id=1,
                service_name="Container handling",
                service_unit="container",
                service_price=Decimal("1200000.00"),
            )
        return None


def build_client(customer: CustomerInfo | None):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_get_contract_service():
        return ContractService(
            customer_client=StubCustomerClient(customer),
            price_client=StubPriceClient(),
        )

    app = FastAPI()
    app.include_router(router, prefix=API_PREFIX)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_contract_service] = override_get_contract_service
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        account_id="sale-1",
        username="sale_user",
        role="ROLE_SALE",
        access_token="test-token",
    )

    return TestClient(app)


def valid_payload():
    return {
        "customer_id": "KH0001",
        "valid_from": "2026-01-01",
        "valid_to": "2026-12-31",
        "payment_terms": "Monthly payment within 15 days",
        "services": [{"service_id": 1, "quantity": 2}],
    }


def active_customer():
    return CustomerInfo(
        id="KH0001",
        name="Samsung Electronics HCMC",
        tax_code="0312345678",
        customer_type="Logistics",
        status="ACTIVE",
    )


def idempotency_headers(key: str = "create-contract-key"):
    return {"Idempotency-Key": key}


def create_contract(client: TestClient, key: str = "create-contract-key"):
    return client.post(
        f"{API_PREFIX}/contracts",
        json=valid_payload(),
        headers=idempotency_headers(key),
    )


def test_post_contracts_creates_draft_contract():
    client = build_client(active_customer())

    response = create_contract(client)

    assert response.status_code == 201
    body = response.json()
    assert body["id"].startswith("HD-")
    assert body["customer_id"] == "KH0001"
    assert body["status"] == "DRAFT"
    assert body["payment_terms"] == "Monthly payment within 15 days"
    assert body["services"][0]["service_id"] == 1
    assert body["services"][0]["service_name"] == "Container handling"
    assert body["services"][0]["quantity"] == 2


def test_post_contracts_returns_not_found_for_missing_customer():
    client = build_client(None)

    response = create_contract(client)

    assert response.status_code == 404
    assert response.json()["detail"] == "customer does not exist"


def test_post_contracts_rejects_invalid_effective_period():
    client = build_client(active_customer())
    payload = valid_payload()
    payload["valid_from"] = "2026-12-31"
    payload["valid_to"] = "2026-01-01"

    response = client.post(
        f"{API_PREFIX}/contracts", json=payload, headers=idempotency_headers()
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "valid_from must not be later than valid_to"


def test_post_contracts_rejects_unknown_service_id():
    client = build_client(active_customer())
    payload = valid_payload()
    payload["services"] = [{"service_id": 999, "quantity": 1}]

    response = client.post(
        f"{API_PREFIX}/contracts", json=payload, headers=idempotency_headers()
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "service_id values are not available: 999"


def test_get_contracts_returns_summaries():
    client = build_client(active_customer())
    create_contract(client)

    response = client.get(f"{API_PREFIX}/contracts")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["contract_id"]
    assert body[0]["customer_name"] == "Samsung Electronics HCMC"
    assert body[0]["total_value"] == "2400000.00"
    assert body[0]["status"] == "DRAFT"


def test_get_contract_detail_returns_services_without_service_id():
    client = build_client(active_customer())
    create_response = create_contract(client)
    contract_id = create_response.json()["id"]

    response = client.get(f"{API_PREFIX}/contracts/{contract_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["contract_id"] == contract_id
    assert body["customer_name"] == "Samsung Electronics HCMC"
    assert body["payment_terms"] == "Monthly payment within 15 days"
    assert body["total_value"] == "2400000.00"
    assert body["updated_at"]
    assert body["services"][0]["service_name"] == "Container handling"
    assert body["services"][0]["quantity"] == 2
    assert "service_id" not in body["services"][0]


def test_get_contract_detail_returns_not_found_for_unknown_contract():
    client = build_client(active_customer())

    response = client.get(f"{API_PREFIX}/contracts/missing-contract")

    assert response.status_code == 404
    assert response.json()["detail"] == "contract does not exist"


def test_health_check_is_versioned():
    from app.main import app as main_app

    client = TestClient(main_app)

    response = client.get(f"{API_PREFIX}/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_contracts_returns_bad_request_when_idempotency_key_is_missing():
    client = build_client(active_customer())

    response = client.post(f"{API_PREFIX}/contracts", json=valid_payload())

    assert response.status_code == 400
    assert response.json()["detail"] == "Idempotency-Key header is required"


def test_post_contracts_returns_same_contract_for_idempotent_retry():
    client = build_client(active_customer())

    first_response = create_contract(client, "same-key")
    retry_response = create_contract(client, "same-key")

    assert retry_response.status_code == 201
    assert retry_response.json()["id"] == first_response.json()["id"]


def test_post_contracts_returns_conflict_for_reused_key_with_different_payload():
    client = build_client(active_customer())
    changed_payload = valid_payload()
    changed_payload["payment_terms"] = "Payment within 30 days"

    create_contract(client, "same-key")
    response = client.post(
        f"{API_PREFIX}/contracts",
        json=changed_payload,
        headers=idempotency_headers("same-key"),
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "idempotency key was already used with a different request"
    )


def test_patch_contract_status_updates_status():
    client = build_client(active_customer())
    create_response = create_contract(client)
    contract_id = create_response.json()["id"]

    response = client.patch(
        f"{API_PREFIX}/contracts/{contract_id}/status",
        json={"status": "SUBMITTED"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "SUBMITTED"


def test_patch_contract_status_rejects_invalid_transition():
    client = build_client(active_customer())
    create_response = create_contract(client)
    contract_id = create_response.json()["id"]

    response = client.patch(
        f"{API_PREFIX}/contracts/{contract_id}/status",
        json={"status": "ACTIVE"},
    )

    assert response.status_code == 422


def test_patch_contract_updates_draft_contract():
    client = build_client(active_customer())
    create_response = create_contract(client)
    contract_id = create_response.json()["id"]
    new_valid_from = date.today() + timedelta(days=30)
    new_valid_to = date.today() + timedelta(days=300)

    response = client.patch(
        f"{API_PREFIX}/contracts/{contract_id}",
        json={
            "valid_from": new_valid_from.isoformat(),
            "valid_to": new_valid_to.isoformat(),
            "payment_terms": "Payment within 30 days",
            "services": [{"service_id": 1, "quantity": 3}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid_from"] == new_valid_from.isoformat()
    assert body["valid_to"] == new_valid_to.isoformat()
    assert body["payment_terms"] == "Payment within 30 days"
    assert body["total_value"] == "3600000.00"
    assert body["services"][0]["quantity"] == 3


def test_delete_contract_deletes_draft_contract():
    client = build_client(active_customer())
    create_response = create_contract(client)
    contract_id = create_response.json()["id"]

    response = client.delete(f"{API_PREFIX}/contracts/{contract_id}")
    detail_response = client.get(f"{API_PREFIX}/contracts/{contract_id}")

    assert response.status_code == 204
    assert detail_response.status_code == 404
