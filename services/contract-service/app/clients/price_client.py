import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol

from app.core.config import get_settings


@dataclass(frozen=True)
class ServicePriceInfo:
    service_id: int
    service_name: str
    service_unit: str
    service_price: Decimal


class PriceClient(Protocol):
    def get_service_price(self, service_id: int) -> ServicePriceInfo | None:
        ...


class PriceClientError(RuntimeError):
    pass


class CacheClient(Protocol):
    def get(self, name: str) -> Any:
        ...

    def setex(self, name: str, time: int, value: str) -> Any:
        ...


class HttpPriceClient:
    def __init__(self, base_url: str, timeout_seconds: float = 5, access_token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.access_token = access_token

    def get_service_price(self, service_id: int) -> ServicePriceInfo | None:
        try:
            import httpx
        except ImportError as exc:
            raise PriceClientError("httpx is required for HttpPriceClient") from exc

        url = f"{self.base_url}/price-lists/effective/services/{service_id}"
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else None
            response = httpx.get(url, headers=headers, timeout=self.timeout_seconds)
        except httpx.HTTPError as exc:
            raise PriceClientError("price service request failed") from exc

        if response.status_code == 404:
            return None

        try:
            response.raise_for_status()
            payload = response.json()
            return ServicePriceInfo(
                service_id=payload["service_id"],
                service_name=payload["service_name"],
                service_unit=payload["unit"],
                service_price=Decimal(str(payload["unit_price"])),
            )
        except (httpx.HTTPStatusError, KeyError, ValueError) as exc:
            raise PriceClientError("price service returned an invalid response") from exc


class CachedPriceClient:
    _key_prefix = "contract:price-service:effective-service-price"

    def __init__(self, inner_client: PriceClient, cache: CacheClient, ttl_seconds: int):
        self.inner_client = inner_client
        self.cache = cache
        self.ttl_seconds = ttl_seconds

    def get_service_price(self, service_id: int) -> ServicePriceInfo | None:
        cache_key = self._cache_key(service_id)
        cached_value = self._get_cached_value(cache_key)
        if cached_value is not None:
            return cached_value

        service_price = self.inner_client.get_service_price(service_id)
        if service_price is not None:
            self._set_cached_value(cache_key, service_price)
        return service_price

    def _cache_key(self, service_id: int) -> str:
        return f"{self._key_prefix}:{service_id}"

    def _get_cached_value(self, cache_key: str) -> ServicePriceInfo | None:
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
            return ServicePriceInfo(
                service_id=payload["service_id"],
                service_name=payload["service_name"],
                service_unit=payload["service_unit"],
                service_price=Decimal(str(payload["service_price"])),
            )
        except (TypeError, KeyError, ValueError, json.JSONDecodeError):
            return None

    def _set_cached_value(
        self, cache_key: str, service_price: ServicePriceInfo
    ) -> None:
        payload = json.dumps(
            {
                "service_id": service_price.service_id,
                "service_name": service_price.service_name,
                "service_unit": service_price.service_unit,
                "service_price": str(service_price.service_price),
            },
            separators=(",", ":"),
        )
        try:
            self.cache.setex(cache_key, self.ttl_seconds, payload)
        except Exception:
            return


class FakePriceClient:
    _services = {
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
        3: ServicePriceInfo(
            service_id=3,
            service_name="Local transportation",
            service_unit="trip",
            service_price=Decimal("2500000.00"),
        ),
    }

    def get_service_price(self, service_id: int) -> ServicePriceInfo | None:
        return self._services.get(service_id)


def get_price_client(access_token: str | None = None) -> PriceClient:
    settings = get_settings()
    if settings.price_client_mode == "http":
        http_client = HttpPriceClient(
            base_url=settings.price_service_url,
            timeout_seconds=settings.price_client_timeout_seconds,
            access_token=access_token,
        )
        if settings.price_cache_enabled:
            try:
                import redis
            except ImportError as exc:
                raise PriceClientError("redis is required for price cache") from exc

            cache = redis.Redis.from_url(settings.redis_url)
            return CachedPriceClient(
                inner_client=http_client,
                cache=cache,
                ttl_seconds=settings.price_cache_ttl_seconds,
            )

        return http_client

    return FakePriceClient()
