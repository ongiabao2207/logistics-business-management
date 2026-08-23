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
from app.routers.contract_router import get_contract_service, router
from app.services.contract_service import ContractService


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
    app.include_router(router)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_contract_service] = override_get_contract_service

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


def test_post_contracts_creates_draft_contract():
    client = build_client(active_customer())

    response = client.post("/contracts", json=valid_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["customer_id"] == "KH0001"
    assert body["status"] == "DRAFT"
    assert body["payment_terms"] == "Monthly payment within 15 days"
    assert body["services"][0]["service_id"] == 1
    assert body["services"][0]["service_name"] == "Container handling"
    assert body["services"][0]["quantity"] == 2


def test_post_contracts_returns_not_found_for_missing_customer():
    client = build_client(None)

    response = client.post("/contracts", json=valid_payload())

    assert response.status_code == 404
    assert response.json()["detail"] == "customer does not exist"


def test_post_contracts_rejects_invalid_effective_period():
    client = build_client(active_customer())
    payload = valid_payload()
    payload["valid_from"] = "2026-12-31"
    payload["valid_to"] = "2026-01-01"

    response = client.post("/contracts", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"] == "valid_from must not be later than valid_to"


def test_post_contracts_rejects_unknown_service_id():
    client = build_client(active_customer())
    payload = valid_payload()
    payload["services"] = [{"service_id": 999, "quantity": 1}]

    response = client.post("/contracts", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"] == "service_id values are not available: 999"


def test_get_contracts_returns_summaries():
    client = build_client(active_customer())
    client.post("/contracts", json=valid_payload())

    response = client.get("/contracts")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["contract_id"]
    assert body[0]["customer_name"] == "Samsung Electronics HCMC"
    assert body[0]["total_value"] == "2400000.00"
    assert body[0]["status"] == "DRAFT"


def test_get_contract_detail_returns_services_without_service_id():
    client = build_client(active_customer())
    create_response = client.post("/contracts", json=valid_payload())
    contract_id = create_response.json()["id"]

    response = client.get(f"/contracts/{contract_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["contract_id"] == contract_id
    assert body["customer_name"] == "Samsung Electronics HCMC"
    assert body["total_value"] == "2400000.00"
    assert body["updated_at"]
    assert body["services"][0]["service_name"] == "Container handling"
    assert body["services"][0]["quantity"] == 2
    assert "service_id" not in body["services"][0]


def test_get_contract_detail_returns_not_found_for_unknown_contract():
    client = build_client(active_customer())

    response = client.get("/contracts/missing-contract")

    assert response.status_code == 404
    assert response.json()["detail"] == "contract does not exist"
