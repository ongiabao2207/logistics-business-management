from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.clients.customer_client import CustomerInfo
from app.db.base import Base
from app.db.session import get_db
from app.routers.contract_router import get_contract_service, router
from app.services.contract_service import ContractService


class StubCustomerClient:
    def __init__(self, customer: CustomerInfo | None) -> None:
        self.customer = customer

    def get_customer(self, customer_id: str) -> CustomerInfo | None:
        return self.customer


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
        return ContractService(customer_client=StubCustomerClient(customer))

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_contract_service] = override_get_contract_service

    return TestClient(app)


def valid_payload():
    return {
        "customer_id": "customer-active",
        "valid_from": "2026-01-01",
        "valid_to": "2026-12-31",
        "payment_terms": "Monthly payment within 15 days",
    }


def test_post_contracts_creates_draft_contract():
    client = build_client(CustomerInfo(id="customer-active", active=True))

    response = client.post("/contracts", json=valid_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["customer_id"] == "customer-active"
    assert body["status"] == "DRAFT"
    assert body["payment_terms"] == "Monthly payment within 15 days"


def test_post_contracts_returns_not_found_for_missing_customer():
    client = build_client(None)

    response = client.post("/contracts", json=valid_payload())

    assert response.status_code == 404
    assert response.json()["detail"] == "customer does not exist"


def test_post_contracts_rejects_invalid_effective_period():
    client = build_client(CustomerInfo(id="customer-active", active=True))
    payload = valid_payload()
    payload["valid_from"] = "2026-12-31"
    payload["valid_to"] = "2026-01-01"

    response = client.post("/contracts", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"] == "valid_from must not be later than valid_to"
