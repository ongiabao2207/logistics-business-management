from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.clients.contract_client import FakeContractClient
from app.db.base import Base
from app.schemas.production_schema import ProductionDetailInput, ProductionPeriodCreate
from app.services.production_service import ProductionService


@pytest.fixture
def service() -> ProductionService:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return ProductionService(Session(engine), FakeContractClient())


def draft_payload(**overrides) -> ProductionPeriodCreate:
    data = {
        "customer_id": "customer-demo", "contract_id": "contract-demo", "period_name": "October 2026",
        "from_date": date(2026, 10, 1), "to_date": date(2026, 10, 31),
        "details": [ProductionDetailInput(service_code="LOADING", recorded_date=date(2026, 10, 2), quantity="12", unit="CONTAINER")],
    }
    data.update(overrides)
    return ProductionPeriodCreate(**data)


def test_creates_draft_and_outbox_event(service: ProductionService) -> None:
    period = service.create_draft(draft_payload(), "operations-1")
    assert period.status == "DRAFT"
    assert len(period.details) == 1


def test_rejects_overlapping_period(service: ProductionService) -> None:
    service.create_draft(draft_payload(), "operations-1")
    with pytest.raises(HTTPException) as error:
        service.create_draft(
            draft_payload(
                from_date=date(2026, 10, 20),
                to_date=date(2026, 11, 5),
                details=[ProductionDetailInput(service_code="LOADING", recorded_date=date(2026, 10, 20), quantity="12", unit="CONTAINER")],
            ),
            "operations-1",
        )
    assert error.value.status_code == 409


def test_locked_period_is_immutable_and_eligible(service: ProductionService) -> None:
    period = service.create_draft(draft_payload(), "operations-1")
    locked = service.lock_period(period.id, "operations-2")
    assert locked.status == "LOCKED"
    assert locked.locked_by == "operations-2"
    with pytest.raises(HTTPException) as error:
        service.replace_details(period.id, draft_payload().details)
    assert error.value.status_code == 409


def test_rejects_record_outside_period(service: ProductionService) -> None:
    payload = draft_payload(details=[ProductionDetailInput(service_code="LOADING", recorded_date=date(2026, 11, 1), quantity="1", unit="CONTAINER")])
    with pytest.raises(HTTPException) as error:
        service.create_draft(payload, "operations-1")
    assert error.value.status_code == 422
