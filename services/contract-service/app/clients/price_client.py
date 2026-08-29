from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

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


class HttpPriceClient:
    def __init__(self, base_url: str, timeout_seconds: float = 5) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def get_service_price(self, service_id: int) -> ServicePriceInfo | None:
        try:
            import httpx
        except ImportError as exc:
            raise PriceClientError("httpx is required for HttpPriceClient") from exc

        url = f"{self.base_url}/price-lists/effective/services/{service_id}"
        try:
            response = httpx.get(url, timeout=self.timeout_seconds)
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


def get_price_client() -> PriceClient:
    settings = get_settings()
    if settings.price_client_mode == "http":
        return HttpPriceClient(
            base_url=settings.price_service_url,
            timeout_seconds=settings.price_client_timeout_seconds,
        )

    return FakePriceClient()
