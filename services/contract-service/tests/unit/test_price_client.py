from decimal import Decimal

import pytest

httpx = pytest.importorskip("httpx")

from app.clients.price_client import HttpPriceClient, PriceClientError


def test_http_price_client_maps_effective_price_response(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert (
            str(request.url)
            == "http://price-service:8001/api/v1/price-lists/effective/services/1"
        )
        return httpx.Response(
            200,
            json={
                "price_list_id": "PL-001",
                "service_id": 1,
                "service_name": "Container handling",
                "unit": "container",
                "unit_price": "1200000.00",
                "effective_from": "2026-01-01",
                "effective_to": "2026-12-31",
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(httpx, "get", client.get)

    price_client = HttpPriceClient("http://price-service:8001/api/v1")

    result = price_client.get_service_price(1)

    assert result.service_id == 1
    assert result.service_name == "Container handling"
    assert result.service_unit == "container"
    assert result.service_price == Decimal("1200000.00")


def test_http_price_client_returns_none_for_missing_effective_price(monkeypatch):
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(404))
    )
    monkeypatch.setattr(httpx, "get", client.get)

    price_client = HttpPriceClient("http://price-service:8001/api/v1")

    assert price_client.get_service_price(999) is None


def test_http_price_client_raises_for_price_service_failure(monkeypatch):
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(500))
    )
    monkeypatch.setattr(httpx, "get", client.get)

    price_client = HttpPriceClient("http://price-service:8001/api/v1")

    with pytest.raises(PriceClientError):
        price_client.get_service_price(1)
