from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.clients.customer_client import CustomerClient, CustomerInfo
from app.clients.price_client import ServicePriceInfo
from app.db.base import Base
from app.models.contract_model import Contract, ContractService as ContractServiceModel
from app.schemas.contract_schema import ContractCreate
from app.services.contract_service import (
    ContractNotFoundError,
    ContractService,
    ContractServiceUnavailableError,
    ContractValidationError,
    CustomerInactiveError,
    CustomerNotFoundError,
    DuplicateContractServiceError,
)


class StubCustomerClient:
    def __init__(
        self,
        customer: CustomerInfo | None = None,
        customers: dict[str, CustomerInfo] | None = None,
    ) -> None:
        self.customer = customer
        self.customers = customers

    def get_customer(self, customer_id: str) -> CustomerInfo | None:
        if self.customers is not None:
            return self.customers.get(customer_id)
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
            CustomerInfo(
                id="customer-active",
                name="Active Customer Co.",
                active=True,
            )
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


def make_contract_service(customer_client: CustomerClient) -> ContractService:
    return ContractService(
        customer_client=customer_client,
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
            CustomerInfo(
                id="customer-inactive",
                name="Inactive Customer Co.",
                active=False,
            )
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


def test_list_contracts_returns_core_information(db_session):
    service = make_service()
    service.create_contract(db_session, make_contract_create(service_ids=[1, 2]))

    contracts = service.list_contracts(db_session)

    assert len(contracts) == 1
    assert contracts[0].customer_name == "Active Customer Co."
    assert contracts[0].total_value == Decimal("1350000.00")
    assert contracts[0].status == "DRAFT"


def test_get_contract_detail_returns_services_without_service_ids(db_session):
    service = make_service()
    contract = service.create_contract(
        db_session, make_contract_create(service_ids=[1, 2])
    )

    detail = service.get_contract_detail(db_session, contract.id)

    assert detail.contract_id == contract.id
    assert detail.customer_name == "Active Customer Co."
    assert detail.total_value == Decimal("1350000.00")
    assert detail.updated_at == contract.updated_at
    assert len(detail.services) == 2
    assert detail.services[0].service_name == "Container handling"
    assert not hasattr(detail.services[0], "service_id")


def test_get_contract_detail_rejects_unknown_contract(db_session):
    service = make_service()

    with pytest.raises(ContractNotFoundError):
        service.get_contract_detail(db_session, "missing-contract")


def test_contract_views_use_unknown_customer_fallback(db_session):
    create_service = make_service()
    create_service.create_contract(db_session, make_contract_create())
    view_service = make_contract_service(StubCustomerClient(None))

    contracts = view_service.list_contracts(db_session)

    assert contracts[0].customer_name == "Unknown Customer"
