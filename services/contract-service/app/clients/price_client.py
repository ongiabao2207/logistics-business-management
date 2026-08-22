from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class ServicePriceInfo:
    service_id: int
    service_name: str
    service_unit: str
    service_price: Decimal


class PriceClient(Protocol):
    def get_service_price(self, service_id: int) -> ServicePriceInfo | None:
        ...


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
    return FakePriceClient()
