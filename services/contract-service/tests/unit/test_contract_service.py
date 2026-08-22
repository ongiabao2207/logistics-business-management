from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.clients.customer_client import CustomerInfo
from app.clients.price_client import ServicePriceInfo
from app.db.base import Base
from app.models.contract_model import Contract, ContractService as ContractServiceModel
from app.schemas.contract_schema import ContractCreate
from app.services.contract_service import (
    ContractService,
    ContractServiceUnavailableError,
    ContractValidationError,
    CustomerInactiveError,
    CustomerNotFoundError,
    DuplicateContractServiceError,
)


class StubCustomerClient:
    def __init__(self, customer: CustomerInfo | None) -> None:
        self.customer = customer

    def get_customer(self, customer_id: str) -> CustomerInfo | None:
        return self.customer


class StubPriceClient:
    def __init__(self, services: dict[int, ServicePriceInfo]) -> None:
        self.services = services

    def get_service_price(self, service_id: int) -> ServicePriceInfo | None:
        return self.services.get(service_id)


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def make_contract_create(**overrides):
    data = {
        "customer_id": "customer-active",
        "valid_from": date(2026, 1, 1),
        "valid_to": date(2026, 12, 31),
        "payment_terms": "Monthly payment within 15 days",
        "service_ids": [1],
    }
    data.update(overrides)
    return ContractCreate(**data)


def make_service() -> ContractService:
    return ContractService(
        customer_client=StubCustomerClient(
            CustomerInfo(id="customer-active", active=True)
        ),
        price_client=StubPriceClient(
            {
                1: ServicePriceInfo(
                    service_id=1,
                    service_name="Container handling",
                    service_unit="container",
                    service_price=Decimal("1200000.00"),
                ),
                2: ServicePriceInfo(
                    service_id=2,
                    service_name="Warehouse storage",
                    service_unit="day",
                    service_price=Decimal("150000.00"),
                ),
            }
        ),
    )


def test_create_contract_saves_draft_with_service_snapshots(db_session):
    service = make_service()

    contract = service.create_contract(
        db_session, make_contract_create(service_ids=[1, 2])
    )

    assert contract.id
    assert contract.status == "DRAFT"
    assert contract.customer_id == "customer-active"
    assert db_session.query(Contract).count() == 1
    assert db_session.query(ContractServiceModel).count() == 2
    assert [service.service_id for service in contract.services] == [1, 2]
    assert contract.services[0].service_name == "Container handling"
    assert str(contract.services[0].service_price) == "1200000.00"


def test_create_contract_rejects_missing_customer(db_session):
    service = ContractService(
        customer_client=StubCustomerClient(None),
        price_client=StubPriceClient({}),
    )

    with pytest.raises(CustomerNotFoundError):
        service.create_contract(db_session, make_contract_create())


def test_create_contract_rejects_inactive_customer(db_session):
    service = ContractService(
        customer_client=StubCustomerClient(
            CustomerInfo(id="customer-inactive", active=False)
        ),
        price_client=StubPriceClient({}),
    )

    with pytest.raises(CustomerInactiveError):
        service.create_contract(db_session, make_contract_create())


def test_create_contract_rejects_invalid_effective_period(db_session):
    service = make_service()

    with pytest.raises(ContractValidationError):
        service.create_contract(
            db_session,
            make_contract_create(
                valid_from=date(2026, 12, 31),
                valid_to=date(2026, 1, 1),
            ),
        )


def test_create_contract_rejects_duplicate_service_ids(db_session):
    service = make_service()

    with pytest.raises(DuplicateContractServiceError):
        service.create_contract(db_session, make_contract_create(service_ids=[1, 1]))


def test_create_contract_rejects_unavailable_service_id(db_session):
    service = make_service()

    with pytest.raises(ContractServiceUnavailableError):
        service.create_contract(db_session, make_contract_create(service_ids=[999]))
