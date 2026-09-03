import pytest

from app.clients.customer_client import (
    CachedCustomerClient,
    CustomerClientError,
    CustomerInfo,
    HttpCustomerClient,
)


class StubInnerCustomerClient:
    def __init__(self, customer: CustomerInfo | None) -> None:
        self.customer = customer
        self.calls = 0

    def get_customer(self, customer_id: str) -> CustomerInfo | None:
        self.calls += 1
        return self.customer


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


def test_http_customer_client_maps_customer_response(monkeypatch):
    httpx = pytest.importorskip("httpx")

    def handler(request):
        assert str(request.url) == "http://customer-service:8000/api/v1/customers/KH0001"
        assert request.headers["authorization"] == "Bearer test-token"
        return httpx.Response(
            200,
            json={
                "id": "KH0001",
                "company_name": "Samsung Electronics HCMC",
                "company_type": "Logistics",
                "tax_code": "0312345678",
                "address": "Ho Chi Minh City",
                "contact_name": "Nguyen Van An",
                "contact_email": "an.nguyen@samsung.example",
                "contact_phone": "0901234567",
                "status": "ACTIVE",
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(httpx, "get", client.get)

    customer_client = HttpCustomerClient(
        "http://customer-service:8000/api/v1",
        access_token="test-token",
    )

    result = customer_client.get_customer("KH0001")

    assert result.id == "KH0001"
    assert result.name == "Samsung Electronics HCMC"
    assert result.customer_type == "Logistics"
    assert result.tax_code == "0312345678"
    assert result.status == "ACTIVE"


def test_http_customer_client_returns_none_for_missing_customer(monkeypatch):
    httpx = pytest.importorskip("httpx")
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(404))
    )
    monkeypatch.setattr(httpx, "get", client.get)

    customer_client = HttpCustomerClient("http://customer-service:8000/api/v1")

    assert customer_client.get_customer("KH9999") is None


def test_http_customer_client_raises_for_customer_service_failure(monkeypatch):
    httpx = pytest.importorskip("httpx")
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(500))
    )
    monkeypatch.setattr(httpx, "get", client.get)

    customer_client = HttpCustomerClient("http://customer-service:8000/api/v1")

    with pytest.raises(CustomerClientError):
        customer_client.get_customer("KH0001")


def test_cached_customer_client_stores_cache_miss_result():
    customer = CustomerInfo(
        id="KH0001",
        name="Samsung Electronics HCMC",
        tax_code="0312345678",
        customer_type="Logistics",
        status="ACTIVE",
    )
    inner_client = StubInnerCustomerClient(customer)
    cache = InMemoryCache()
    customer_client = CachedCustomerClient(inner_client, cache, ttl_seconds=1800)

    result = customer_client.get_customer("KH0001")

    assert result == customer
    assert inner_client.calls == 1
    cache_key = "contract:customer-service:customer:KH0001"
    assert cache_key in cache.values
    assert cache.ttls[cache_key] == 1800


def test_cached_customer_client_uses_cache_hit_without_calling_inner_client():
    cache = InMemoryCache()
    cache.values["contract:customer-service:customer:KH0001"] = (
        '{"id":"KH0001","name":"Samsung Electronics HCMC",'
        '"tax_code":"0312345678","customer_type":"Logistics","status":"ACTIVE"}'
    )
    inner_client = StubInnerCustomerClient(None)
    customer_client = CachedCustomerClient(inner_client, cache, ttl_seconds=1800)

    result = customer_client.get_customer("KH0001")

    assert result.id == "KH0001"
    assert result.name == "Samsung Electronics HCMC"
    assert inner_client.calls == 0


def test_cached_customer_client_does_not_cache_missing_customer():
    inner_client = StubInnerCustomerClient(None)
    cache = InMemoryCache()
    customer_client = CachedCustomerClient(inner_client, cache, ttl_seconds=1800)

    result = customer_client.get_customer("KH9999")

    assert result is None
    assert inner_client.calls == 1
    assert cache.values == {}


def test_cached_customer_client_ignores_cache_failure_when_inner_client_succeeds():
    customer = CustomerInfo(
        id="KH0001",
        name="Samsung Electronics HCMC",
        tax_code="0312345678",
        customer_type="Logistics",
        status="ACTIVE",
    )
    inner_client = StubInnerCustomerClient(customer)
    cache = InMemoryCache(fail=True)
    customer_client = CachedCustomerClient(inner_client, cache, ttl_seconds=1800)

    result = customer_client.get_customer("KH0001")

    assert result == customer
    assert inner_client.calls == 1
