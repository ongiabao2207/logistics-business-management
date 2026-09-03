import json
from dataclasses import dataclass
from typing import Any, Protocol

from app.core.config import get_settings


@dataclass(frozen=True)
class CustomerInfo:
    id: str
    name: str
    tax_code: str
    customer_type: str
    status: str


class CustomerClient(Protocol):
    def get_customer(self, customer_id: str) -> CustomerInfo | None:
        ...


class CustomerClientError(RuntimeError):
    pass


class CacheClient(Protocol):
    def get(self, name: str) -> Any:
        ...

    def setex(self, name: str, time: int, value: str) -> Any:
        ...


class HttpCustomerClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 5,
        access_token: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.access_token = access_token

    def get_customer(self, customer_id: str) -> CustomerInfo | None:
        try:
            import httpx
        except ImportError as exc:
            raise CustomerClientError("httpx is required for HttpCustomerClient") from exc

        url = f"{self.base_url}/customers/{customer_id}"
        headers = (
            {"Authorization": f"Bearer {self.access_token}"}
            if self.access_token
            else None
        )
        try:
            response = httpx.get(url, headers=headers, timeout=self.timeout_seconds)
        except httpx.HTTPError as exc:
            raise CustomerClientError("customer service request failed") from exc

        if response.status_code == 404:
            return None

        try:
            response.raise_for_status()
            payload = response.json()
            return CustomerInfo(
                id=payload["id"],
                name=payload["company_name"],
                tax_code=payload["tax_code"],
                customer_type=payload["company_type"],
                status=payload["status"],
            )
        except (httpx.HTTPStatusError, KeyError, ValueError) as exc:
            raise CustomerClientError(
                "customer service returned an invalid response"
            ) from exc


class CachedCustomerClient:
    _key_prefix = "contract:customer-service:customer"

    def __init__(
        self,
        inner_client: CustomerClient,
        cache: CacheClient,
        ttl_seconds: int,
    ) -> None:
        self.inner_client = inner_client
        self.cache = cache
        self.ttl_seconds = ttl_seconds

    def get_customer(self, customer_id: str) -> CustomerInfo | None:
        cache_key = self._cache_key(customer_id)
        cached_value = self._get_cached_value(cache_key)
        if cached_value is not None:
            return cached_value

        customer = self.inner_client.get_customer(customer_id)
        if customer is not None:
            self._set_cached_value(cache_key, customer)
        return customer

    def _cache_key(self, customer_id: str) -> str:
        return f"{self._key_prefix}:{customer_id}"

    def _get_cached_value(self, cache_key: str) -> CustomerInfo | None:
        try:
            raw_value = self.cache.get(cache_key)
        except Exception:
            return None

        if raw_value is None:
            return None

        if isinstance(raw_value, bytes):
            raw_value = raw_value.decode("utf-8")

        try:
            payload = json.loads(raw_value)
            return CustomerInfo(
                id=payload["id"],
                name=payload["name"],
                tax_code=payload["tax_code"],
                customer_type=payload["customer_type"],
                status=payload["status"],
            )
        except (TypeError, KeyError, ValueError, json.JSONDecodeError):
            return None

    def _set_cached_value(self, cache_key: str, customer: CustomerInfo) -> None:
        payload = json.dumps(
            {
                "id": customer.id,
                "name": customer.name,
                "tax_code": customer.tax_code,
                "customer_type": customer.customer_type,
                "status": customer.status,
            },
            separators=(",", ":"),
        )
        try:
            self.cache.setex(cache_key, self.ttl_seconds, payload)
        except Exception:
            return


class FakeCustomerClient:
    _customers = {
        "KH0001": CustomerInfo(
            id="KH0001",
            name="Samsung Electronics HCMC",
            tax_code="0312345678",
            customer_type="Logistics",
            status="ACTIVE",
        ),
        "KH0002": CustomerInfo(
            id="KH0002",
            name="Vinamilk",
            tax_code="0300588569",
            customer_type="FMCG",
            status="ACTIVE",
        ),
        "KH0003": CustomerInfo(
            id="KH0003",
            name="Thaco Logistics",
            tax_code="4000123456",
            customer_type="Logistics",
            status="ACTIVE",
        ),
        "KH0004": CustomerInfo(
            id="KH0004",
            name="Nestlé Việt Nam",
            tax_code="0302012345",
            customer_type="FMCG",
            status="ACTIVE",
        ),
        "KH0005": CustomerInfo(
            id="KH0005",
            name="Intel Products Vietnam",
            tax_code="0309876543",
            customer_type="Manufacturing",
            status="ACTIVE",
        ),
    }

    def get_customer(self, customer_id: str) -> CustomerInfo | None:
        return self._customers.get(customer_id)


def get_customer_client(access_token: str | None = None) -> CustomerClient:
    settings = get_settings()
    if settings.customer_client_mode == "http":
        http_client = HttpCustomerClient(
            base_url=settings.customer_service_url,
            timeout_seconds=settings.customer_client_timeout_seconds,
            access_token=access_token,
        )
        if settings.customer_cache_enabled:
            try:
                import redis
            except ImportError as exc:
                raise CustomerClientError(
                    "redis is required for customer cache"
                ) from exc

            cache = redis.Redis.from_url(settings.redis_url)
            return CachedCustomerClient(
                inner_client=http_client,
                cache=cache,
                ttl_seconds=settings.customer_cache_ttl_seconds,
            )

        return http_client

    return FakeCustomerClient()
