from datetime import date
from decimal import Decimal

import httpx

from app.clients.contracts import HttpContractClient
from app.clients.prices import HttpPriceClient
from app.clients.production import HttpProductionClient


def response(payload) -> httpx.Response:
    return httpx.Response(200, json=payload, request=httpx.Request("GET", "http://upstream"))


def test_contract_client_reads_real_contract_shape(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: response({
        "contract_id": "HD2026004", "customer_id": "KH0001",
        "valid_from": "2026-01-01", "valid_to": "2026-12-31", "status": "ACTIVE",
    }))
    contract = HttpContractClient("http://contract/api/v1", "token").get_contract("HD2026004", "KH0001")
    assert contract.customer_id == "KH0001"
    assert contract.status == "ACTIVE"


def test_production_client_reads_only_exact_locked_period(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: response([{
        "contract_id": "HD2026004", "from_date": "2026-09-01", "to_date": "2026-09-30",
        "status": "LOCKED", "details": [{"service_code": "1", "quantity": "12.000", "notes": "Bốc xếp"}],
    }]))
    records = HttpProductionClient("http://production/api/v1", "token").get_eligible_records(
        "HD2026004", date(2026, 9, 1), date(2026, 9, 30)
    )
    assert records[0].service_id == "1"
    assert records[0].quantity == Decimal("12.000")
    assert records[0].status == "LOCKED"


def test_production_client_excludes_draft_and_different_periods(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: response([
        {
            "contract_id": "HD2026004", "from_date": "2026-09-01", "to_date": "2026-09-30",
            "status": "DRAFT", "details": [{"service_code": "1", "quantity": "12"}],
        },
        {
            "contract_id": "HD2026004", "from_date": "2026-09-05", "to_date": "2026-09-20",
            "status": "LOCKED", "details": [{"service_code": "1", "quantity": "8"}],
        },
    ]))

    records = HttpProductionClient("http://production/api/v1", "token").get_eligible_records(
        "HD2026004", date(2026, 9, 1), date(2026, 9, 30)
    )

    assert records == []


def test_price_client_uses_price_effective_on_payment_date(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: response([{
        "id": "BG-PAYMENT-2026", "status": "EFFECTIVE",
        "effective_from": "2026-01-01", "effective_to": "2026-12-31",
        "details": [{"service_id": 1, "unit_price": "350000.00"}],
    }]))
    price = HttpPriceClient("http://price/api/v1", "token").get_effective_price(
        "HD2026004", "1", date(2026, 9, 30)
    )
    assert price == Decimal("350000.00")
