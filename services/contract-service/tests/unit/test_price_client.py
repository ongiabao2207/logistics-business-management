from decimal import Decimal

import pytest

from app.clients.price_client import (
    CachedPriceClient,
    HttpPriceClient,
    PriceClientError,
    ServicePriceInfo,
)


class StubInnerPriceClient:
    def __init__(self, service_price: ServicePriceInfo | None) -> None:
        self.service_price = service_price
        self.calls = 0

    def get_service_price(self, service_id: int) -> ServicePriceInfo | None:
        self.calls += 1
        return self.service_price


class InMemoryCache:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    def get(self, name: str):
        if self.fail:
            raise RuntimeError("cache unavailable")
        return self.values.get(name)

    def setex(self, name: str, time: int, value: str):
        if self.fail:
            raise RuntimeError("cache unavailable")
        self.values[name] = value
        self.ttls[name] = time


def test_http_price_client_maps_effective_price_response(monkeypatch):
    httpx = pytest.importorskip("httpx")

    def handler(request):
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
    httpx = pytest.importorskip("httpx")

    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(404))
    )
    monkeypatch.setattr(httpx, "get", client.get)

    price_client = HttpPriceClient("http://price-service:8001/api/v1")

    assert price_client.get_service_price(999) is None


def test_http_price_client_raises_for_price_service_failure(monkeypatch):
    httpx = pytest.importorskip("httpx")

    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(500))
    )
    monkeypatch.setattr(httpx, "get", client.get)

    price_client = HttpPriceClient("http://price-service:8001/api/v1")

    with pytest.raises(PriceClientError):
        price_client.get_service_price(1)


def test_cached_price_client_stores_cache_miss_result():
    service_price = ServicePriceInfo(
        service_id=1,
        service_name="Bốc xếp Container 20ft",
        service_unit="Container",
        service_price=Decimal("350000.00"),
    )
    inner_client = StubInnerPriceClient(service_price)
    cache = InMemoryCache()
    price_client = CachedPriceClient(inner_client, cache, ttl_seconds=300)

    result = price_client.get_service_price(1)

    assert result == service_price
    assert inner_client.calls == 1
    cache_key = "contract:price-service:effective-service-price:1"
    assert cache_key in cache.values
    assert cache.ttls[cache_key] == 300


def test_cached_price_client_uses_cache_hit_without_calling_inner_client():
    cache = InMemoryCache()
    cache.values["contract:price-service:effective-service-price:1"] = (
        '{"service_id":1,"service_name":"Bốc xếp Container 20ft",'
        '"service_unit":"Container","service_price":"350000.00"}'
    )
    inner_client = StubInnerPriceClient(None)
    price_client = CachedPriceClient(inner_client, cache, ttl_seconds=300)

    result = price_client.get_service_price(1)

    assert result.service_id == 1
    assert result.service_name == "Bốc xếp Container 20ft"
    assert result.service_unit == "Container"
    assert result.service_price == Decimal("350000.00")
    assert inner_client.calls == 0


def test_cached_price_client_does_not_cache_missing_service_price():
    inner_client = StubInnerPriceClient(None)
    cache = InMemoryCache()
    price_client = CachedPriceClient(inner_client, cache, ttl_seconds=300)

    result = price_client.get_service_price(999)

    assert result is None
    assert inner_client.calls == 1
    assert cache.values == {}


def test_cached_price_client_ignores_cache_failure_when_inner_client_succeeds():
    service_price = ServicePriceInfo(
        service_id=1,
        service_name="Bốc xếp Container 20ft",
        service_unit="Container",
        service_price=Decimal("350000.00"),
    )
    inner_client = StubInnerPriceClient(service_price)
    cache = InMemoryCache(fail=True)
    price_client = CachedPriceClient(inner_client, cache, ttl_seconds=300)

    result = price_client.get_service_price(1)

    assert result == service_price
    assert inner_client.calls == 1
