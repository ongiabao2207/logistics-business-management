from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.clients.customer_client import CustomerInfo
from app.db.base import Base
from app.models.contract_model import Contract
from app.schemas.contract_schema import ContractCreate
from app.services.contract_service import (
    ContractService,
    ContractValidationError,
    CustomerInactiveError,
    CustomerNotFoundError,
)


class StubCustomerClient:
    def __init__(self, customer: CustomerInfo | None) -> None:
        self.customer = customer

    def get_customer(self, customer_id: str) -> CustomerInfo | None:
        return self.customer


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
    }
    data.update(overrides)
    return ContractCreate(**data)


def test_create_contract_saves_draft(db_session):
    service = ContractService(
        customer_client=StubCustomerClient(
            CustomerInfo(id="customer-active", active=True)
        )
    )

    contract = service.create_contract(db_session, make_contract_create())

    assert contract.id
    assert contract.status == "DRAFT"
    assert contract.customer_id == "customer-active"
    assert db_session.query(Contract).count() == 1


def test_create_contract_rejects_missing_customer(db_session):
    service = ContractService(customer_client=StubCustomerClient(None))

    with pytest.raises(CustomerNotFoundError):
        service.create_contract(db_session, make_contract_create())


def test_create_contract_rejects_inactive_customer(db_session):
    service = ContractService(
        customer_client=StubCustomerClient(
            CustomerInfo(id="customer-inactive", active=False)
        )
    )

    with pytest.raises(CustomerInactiveError):
        service.create_contract(db_session, make_contract_create())


def test_create_contract_rejects_invalid_effective_period(db_session):
    service = ContractService(
        customer_client=StubCustomerClient(
            CustomerInfo(id="customer-active", active=True)
        )
    )

    with pytest.raises(ContractValidationError):
        service.create_contract(
            db_session,
            make_contract_create(
                valid_from=date(2026, 12, 31),
                valid_to=date(2026, 1, 1),
            ),
        )
