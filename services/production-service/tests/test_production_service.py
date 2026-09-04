from datetime import date
import json

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.clients.contract_client import FakeContractClient
from app.db.base import Base
from app.models.production_model import OutboxEvent
from app.schemas.production_schema import ProductionDetailInput, ProductionPeriodCreate
from app.services.production_service import ProductionService


@pytest.fixture
def service() -> ProductionService:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return ProductionService(Session(engine), FakeContractClient())


def draft_payload(**overrides) -> ProductionPeriodCreate:
    data = {
        "customer_id": "KH-TCB-001", "contract_id": "HD-2024-TCB-082",
        "from_date": date(2024, 10, 1), "to_date": date(2024, 10, 31),
        "details": [ProductionDetailInput(service_code="LOADING", recorded_date=date(2024, 10, 2), quantity="12", unit="CONTAINER")],
    }
    data.update(overrides)
    return ProductionPeriodCreate(**data)


def test_creates_draft_and_outbox_event(service: ProductionService) -> None:
    period = service.create_draft(draft_payload(), "operations-1")
    assert period.status == "DRAFT"
    assert period.period_name == "SL-2024-001"
    assert len(period.details) == 1


def test_period_codes_increment_within_the_contract_year(service: ProductionService) -> None:
    first = service.create_draft(draft_payload(), "operations-1")
    second = service.create_draft(
        draft_payload(
            from_date=date(2024, 11, 1),
            to_date=date(2024, 11, 30),
            details=[ProductionDetailInput(service_code="LOADING", recorded_date=date(2024, 11, 2), quantity="12", unit="CONTAINER")],
        ),
        "operations-1",
    )

    assert first.period_name == "SL-2024-001"
    assert second.period_name == "SL-2024-002"


def test_rejects_overlapping_period(service: ProductionService) -> None:
    service.create_draft(draft_payload(), "operations-1")
    with pytest.raises(HTTPException) as error:
        service.create_draft(
            draft_payload(
                from_date=date(2024, 10, 20),
                to_date=date(2024, 11, 5),
                details=[ProductionDetailInput(service_code="LOADING", recorded_date=date(2024, 10, 20), quantity="12", unit="CONTAINER")],
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


def test_lock_event_has_accountant_friendly_notification_text(service: ProductionService) -> None:
    period = service.create_draft(draft_payload(), "operations-1")
    service.lock_period(period.id, "operations-2")

    event = service.db.query(OutboxEvent).filter_by(event_type="PRODUCTION_PERIOD_LOCKED").one()
    payload = json.loads(event.payload)

    assert payload["title"] == "Kỳ sản lượng đã được khóa"
    assert payload["content"] == "Kỳ sản lượng SL-2024-001 thuộc hợp đồng HD-2024-TCB-082 đã được khóa."
    assert payload["recipient_role"] == "ROLE_ACCOUNTANT"


def test_accountant_sees_only_locked_periods(service: ProductionService) -> None:
    draft = service.create_draft(draft_payload(), "operations-1")
    service.create_draft(
        draft_payload(
            from_date=date(2024, 11, 1),
            to_date=date(2024, 11, 30),
            details=[ProductionDetailInput(service_code="LOADING", recorded_date=date(2024, 11, 2), quantity="12", unit="CONTAINER")],
        ),
        "operations-1",
    )
    service.lock_period(draft.id, "operations-1")

    visible = service.list_periods(None, None, "ROLE_ACCOUNTANT")

    assert [period.id for period in visible] == [draft.id]
    with pytest.raises(HTTPException) as error:
        service.get_period(2, "ROLE_ACCOUNTANT")
    assert error.value.status_code == 404


def test_rejects_record_outside_period(service: ProductionService) -> None:
    payload = draft_payload(details=[ProductionDetailInput(service_code="LOADING", recorded_date=date(2024, 11, 1), quantity="1", unit="CONTAINER")])
    with pytest.raises(HTTPException) as error:
        service.create_draft(payload, "operations-1")
    assert error.value.status_code == 422
