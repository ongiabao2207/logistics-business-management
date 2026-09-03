from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.clients.customer_client import CustomerClient, CustomerInfo, FakeCustomerClient
from app.clients.price_client import PriceClientError, ServicePriceInfo
from app.crud.contract_crud import ContractCRUD
from app.db.base import Base
from app.models.contract_model import (
    Contract,
    ContractService as ContractServiceModel,
    ContractYearSequence,
)
from app.schemas.contract_schema import (
    ContractCreate,
    ContractStatusUpdate,
    ContractUpdate,
)
from app.services.contract_service import (
    ContractNotDeletableError,
    ContractNotEditableError,
    ContractNotFoundError,
    ContractNumberLimitError,
    ContractService,
    ContractServiceUnavailableError,
    ContractValidationError,
    CustomerInactiveError,
    CustomerNotFoundError,
    DuplicateContractServiceError,
    IdempotencyConflictError,
    InvalidContractStatusTransitionError,
    PriceServiceDependencyError,
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


class FailingPriceClient:
    def get_service_price(self, service_id: int) -> ServicePriceInfo | None:
        raise PriceClientError("price service exploded")


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
        "customer_id": "KH0001",
        "valid_from": date.today() + timedelta(days=30),
        "valid_to": date.today() + timedelta(days=300),
        "payment_terms": "Monthly payment within 15 days",
        "services": [{"service_id": 1, "quantity": 2}],
    }
    data.update(overrides)
    return ContractCreate(**data)


def customer_info(
    customer_id: str = "KH0001",
    name: str = "Samsung Electronics HCMC",
    status: str = "ACTIVE",
) -> CustomerInfo:
    return CustomerInfo(
        id=customer_id,
        name=name,
        tax_code="0312345678",
        customer_type="Logistics",
        status=status,
    )


def price_client() -> StubPriceClient:
    return StubPriceClient(
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
    )


def make_service() -> ContractService:
    return ContractService(
        customer_client=StubCustomerClient(customer_info()),
        price_client=price_client(),
    )


def make_service_for_year(year: int) -> ContractService:
    return ContractService(
        customer_client=StubCustomerClient(customer_info()),
        price_client=price_client(),
        crud=ContractCRUD(current_year=lambda: year),
    )


def make_contract_service(customer_client: CustomerClient) -> ContractService:
    return ContractService(
        customer_client=customer_client,
        price_client=price_client(),
    )


def multi_service_payload():
    return [
        {"service_id": 1, "quantity": 2},
        {"service_id": 2, "quantity": 3},
    ]


def test_create_contract_saves_draft_with_service_snapshots(db_session):
    service = make_service()

    contract = service.create_contract(
        db_session,
        make_contract_create(services=multi_service_payload()),
        "create-contract-1",
    )

    assert contract.id == f"HD-{date.today().year}-001"
    assert contract.status == "DRAFT"
    assert contract.customer_id == "KH0001"
    assert db_session.query(Contract).count() == 1
    assert db_session.query(ContractServiceModel).count() == 2
    assert [service.service_id for service in contract.services] == [1, 2]
    assert [service.quantity for service in contract.services] == [2, 3]
    assert contract.services[0].service_name == "Container handling"
    assert str(contract.services[0].service_price) == "1200000.00"


def test_create_contract_rejects_missing_customer(db_session):
    service = ContractService(
        customer_client=StubCustomerClient(None),
        price_client=StubPriceClient({}),
    )

    with pytest.raises(CustomerNotFoundError):
        service.create_contract(db_session, make_contract_create(), "missing-customer")


def test_create_contract_rejects_inactive_customer(db_session):
    service = ContractService(
        customer_client=StubCustomerClient(
            customer_info(customer_id="KH9999", name="Locked Customer", status="LOCKED")
        ),
        price_client=StubPriceClient({}),
    )

    with pytest.raises(CustomerInactiveError):
        service.create_contract(db_session, make_contract_create(), "inactive-customer")


def test_create_contract_rejects_non_future_valid_from(db_session):
    service = make_service()

    with pytest.raises(ContractValidationError) as exc:
        service.create_contract(
            db_session,
            make_contract_create(
                valid_from=date.today(),
                valid_to=date.today() + timedelta(days=30),
            ),
            "today-start",
        )

    assert str(exc.value) == "valid_from must be greater than current date"


def test_create_contract_rejects_valid_to_before_valid_from(db_session):
    service = make_service()
    valid_from = date.today() + timedelta(days=30)

    with pytest.raises(ContractValidationError) as exc:
        service.create_contract(
            db_session,
            make_contract_create(
                valid_from=valid_from,
                valid_to=valid_from - timedelta(days=1),
            ),
            "invalid-period",
        )

    assert str(exc.value) == "valid_to must be on or after valid_from"


def test_create_contract_allows_same_valid_from_and_valid_to(db_session):
    service = make_service()
    valid_from = date.today() + timedelta(days=30)

    contract = service.create_contract(
        db_session,
        make_contract_create(valid_from=valid_from, valid_to=valid_from),
        "single-day-contract",
    )

    assert contract.valid_from == valid_from
    assert contract.valid_to == valid_from


def test_create_contract_rejects_duplicate_service_ids(db_session):
    service = make_service()

    with pytest.raises(DuplicateContractServiceError):
        service.create_contract(
            db_session,
            make_contract_create(
                services=[
                    {"service_id": 1, "quantity": 2},
                    {"service_id": 1, "quantity": 3},
                ]
            ),
            "duplicate-service",
        )


def test_create_contract_rejects_unavailable_service_id(db_session):
    service = make_service()

    with pytest.raises(ContractServiceUnavailableError):
        service.create_contract(
            db_session,
            make_contract_create(services=[{"service_id": 999, "quantity": 1}]),
            "unavailable-service",
        )


def test_create_contract_reports_price_service_dependency_failure(db_session):
    service = ContractService(
        customer_client=StubCustomerClient(customer_info()),
        price_client=FailingPriceClient(),
    )

    with pytest.raises(PriceServiceDependencyError):
        service.create_contract(db_session, make_contract_create(), "price-failure")


def test_create_contract_rejects_non_positive_quantity():
    with pytest.raises(ValueError):
        make_contract_create(services=[{"service_id": 1, "quantity": 0}])


def test_list_contracts_returns_core_information(db_session):
    service = make_service()
    service.create_contract(
        db_session,
        make_contract_create(services=multi_service_payload()),
        "list-contracts",
    )

    contracts = service.list_contracts(db_session)

    assert len(contracts) == 1
    assert contracts[0].customer_name == "Samsung Electronics HCMC"
    assert contracts[0].total_value == Decimal("2850000.00")
    assert contracts[0].status == "DRAFT"


def test_get_contract_detail_returns_services_without_service_ids(db_session):
    service = make_service()
    contract = service.create_contract(
        db_session,
        make_contract_create(services=multi_service_payload()),
        "get-detail",
    )

    detail = service.get_contract_detail(db_session, contract.id)

    assert detail.contract_id == contract.id
    assert detail.customer_name == "Samsung Electronics HCMC"
    assert detail.payment_terms == "Monthly payment within 15 days"
    assert detail.total_value == Decimal("2850000.00")
    assert detail.updated_at == contract.updated_at
    assert len(detail.services) == 2
    assert detail.services[0].service_name == "Container handling"
    assert detail.services[0].quantity == 2
    assert not hasattr(detail.services[0], "service_id")


def test_get_contract_detail_rejects_unknown_contract(db_session):
    service = make_service()

    with pytest.raises(ContractNotFoundError):
        service.get_contract_detail(db_session, "missing-contract")


def test_contract_views_use_unknown_customer_fallback(db_session):
    create_service = make_service()
    create_service.create_contract(db_session, make_contract_create(), "unknown-customer")
    view_service = make_contract_service(StubCustomerClient(None))

    contracts = view_service.list_contracts(db_session)

    assert contracts[0].customer_name == "Unknown Customer"


def test_create_contract_increments_yearly_contract_id_sequence(db_session):
    service = make_service_for_year(2026)

    first_contract = service.create_contract(
        db_session, make_contract_create(), "create-2026-1"
    )
    second_contract = service.create_contract(
        db_session, make_contract_create(), "create-2026-2"
    )

    assert first_contract.id == "HD-2026-001"
    assert second_contract.id == "HD-2026-002"


def test_create_contract_resets_contract_id_sequence_for_new_year(db_session):
    service_2026 = make_service_for_year(2026)
    service_2027 = make_service_for_year(2027)

    service_2026.create_contract(db_session, make_contract_create(), "create-2026")
    contract_2027 = service_2027.create_contract(
        db_session, make_contract_create(), "create-2027"
    )

    assert contract_2027.id == "HD-2027-001"


def test_create_contract_is_idempotent_for_same_key_and_payload(db_session):
    service = make_service_for_year(2026)
    contract_in = make_contract_create()

    first_contract = service.create_contract(db_session, contract_in, "same-key")
    retry_contract = service.create_contract(db_session, contract_in, "same-key")

    assert first_contract.id == "HD-2026-001"
    assert retry_contract.id == first_contract.id
    assert db_session.query(Contract).count() == 1


def test_create_contract_rejects_same_idempotency_key_with_different_payload(
    db_session,
):
    service = make_service_for_year(2026)

    service.create_contract(db_session, make_contract_create(), "same-key")

    with pytest.raises(IdempotencyConflictError):
        service.create_contract(
            db_session,
            make_contract_create(payment_terms="Payment within 30 days"),
            "same-key",
        )


def test_create_contract_rejects_when_yearly_contract_number_limit_is_reached(
    db_session,
):
    service = make_service_for_year(2026)
    db_session.add(ContractYearSequence(year=2026, last_number=999))
    db_session.commit()

    with pytest.raises(ContractNumberLimitError):
        service.create_contract(db_session, make_contract_create(), "limit-reached")


def test_update_contract_status_allows_expected_lifecycle_transitions(db_session):
    service = make_service()
    contract = service.create_contract(db_session, make_contract_create(), "status-flow")

    submitted = service.update_contract_status(
        db_session, contract.id, ContractStatusUpdate(status="SUBMITTED")
    )
    active = service.update_contract_status(
        db_session, contract.id, ContractStatusUpdate(status="ACTIVE")
    )
    expired = service.update_contract_status(
        db_session, contract.id, ContractStatusUpdate(status="EXPIRED")
    )

    assert submitted.status == "SUBMITTED"
    assert active.status == "ACTIVE"
    assert expired.status == "EXPIRED"


def test_update_contract_status_rejects_invalid_transition(db_session):
    service = make_service()
    contract = service.create_contract(db_session, make_contract_create(), "bad-status")

    with pytest.raises(InvalidContractStatusTransitionError):
        service.update_contract_status(
            db_session, contract.id, ContractStatusUpdate(status="ACTIVE")
        )


def test_update_contract_modifies_draft_dates_and_replaces_services(db_session):
    service = make_service()
    contract = service.create_contract(db_session, make_contract_create(), "update-info")
    new_valid_from = date.today() + timedelta(days=30)
    new_valid_to = date.today() + timedelta(days=300)

    updated = service.update_contract(
        db_session,
        contract.id,
        ContractUpdate(
            valid_from=new_valid_from,
            valid_to=new_valid_to,
            payment_terms="Payment within 30 days",
            services=[{"service_id": 2, "quantity": 4}],
        ),
    )

    persisted_contract = db_session.get(Contract, contract.id)

    assert updated.valid_from == new_valid_from
    assert updated.valid_to == new_valid_to
    assert updated.payment_terms == "Payment within 30 days"
    assert updated.total_value == Decimal("600000.00")
    assert len(updated.services) == 1
    assert updated.services[0].service_name == "Warehouse storage"
    assert updated.services[0].quantity == 4
    assert persisted_contract.payment_terms == "Payment within 30 days"
    assert persisted_contract.updated_at == updated.updated_at
    assert db_session.query(ContractServiceModel).count() == 1


def test_update_contract_rejects_non_draft_contract(db_session):
    service = make_service()
    contract = service.create_contract(db_session, make_contract_create(), "non-draft")
    new_valid_from = date.today() + timedelta(days=30)
    service.update_contract_status(
        db_session, contract.id, ContractStatusUpdate(status="SUBMITTED")
    )

    with pytest.raises(ContractNotEditableError):
        service.update_contract(
            db_session,
            contract.id,
            ContractUpdate(valid_from=new_valid_from),
        )


def test_update_contract_rejects_non_future_valid_from(db_session):
    service = make_service()
    contract = service.create_contract(db_session, make_contract_create(), "bad-from")

    with pytest.raises(ContractValidationError) as exc:
        service.update_contract(
            db_session,
            contract.id,
            ContractUpdate(
                valid_from=date.today(),
                valid_to=date.today() + timedelta(days=30),
            ),
        )

    assert str(exc.value) == "valid_from must be greater than current date"


def test_update_contract_rejects_valid_to_before_valid_from(db_session):
    service = make_service()
    contract = service.create_contract(db_session, make_contract_create(), "bad-to")
    new_valid_from = date.today() + timedelta(days=30)

    with pytest.raises(ContractValidationError) as exc:
        service.update_contract(
            db_session,
            contract.id,
            ContractUpdate(
                valid_from=new_valid_from,
                valid_to=new_valid_from - timedelta(days=1),
            ),
        )

    assert str(exc.value) == "valid_to must be on or after valid_from"


def test_update_contract_allows_same_valid_from_and_valid_to(db_session):
    service = make_service()
    contract = service.create_contract(db_session, make_contract_create(), "same-day")
    new_valid_from = date.today() + timedelta(days=30)

    updated = service.update_contract(
        db_session,
        contract.id,
        ContractUpdate(valid_from=new_valid_from, valid_to=new_valid_from),
    )

    assert updated.valid_from == new_valid_from
    assert updated.valid_to == new_valid_from


def test_update_contract_updates_parent_timestamp_for_service_only_change(db_session):
    service = make_service()
    contract = service.create_contract(
        db_session,
        make_contract_create(
            valid_from=date.today() + timedelta(days=30),
            valid_to=date.today() + timedelta(days=300),
        ),
        "service-only",
    )
    original_updated_at = contract.updated_at

    updated = service.update_contract(
        db_session,
        contract.id,
        ContractUpdate(services=[{"service_id": 2, "quantity": 4}]),
    )

    assert updated.updated_at > original_updated_at


def test_update_contract_rejects_unknown_service_id(db_session):
    service = make_service()
    contract = service.create_contract(
        db_session,
        make_contract_create(
            valid_from=date.today() + timedelta(days=30),
            valid_to=date.today() + timedelta(days=300),
        ),
        "unknown-update-service",
    )

    with pytest.raises(ContractServiceUnavailableError):
        service.update_contract(
            db_session,
            contract.id,
            ContractUpdate(services=[{"service_id": 999, "quantity": 1}]),
        )


def test_delete_contract_removes_draft_contract_and_services(db_session):
    service = make_service()
    contract = service.create_contract(db_session, make_contract_create(), "delete")

    service.delete_contract(db_session, contract.id)

    assert db_session.query(Contract).count() == 0
    assert db_session.query(ContractServiceModel).count() == 0


def test_delete_contract_rejects_non_draft_contract(db_session):
    service = make_service()
    contract = service.create_contract(db_session, make_contract_create(), "no-delete")
    service.update_contract_status(
        db_session, contract.id, ContractStatusUpdate(status="SUBMITTED")
    )

    with pytest.raises(ContractNotDeletableError):
        service.delete_contract(db_session, contract.id)


def test_fake_customer_client_only_accepts_sample_customer_ids():
    client = FakeCustomerClient()

    assert client.get_customer("KH0001") is not None
    assert client.get_customer("customer-active") is None
    assert client.get_customer("KH9999") is None
