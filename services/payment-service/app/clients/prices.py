from datetime import date
from decimal import Decimal
from typing import Protocol


class PriceClient(Protocol):
    def get_effective_price(self, contract_id: str, service_id: str, business_date: date) -> Decimal: ...


class FakePriceClient:
    prices = {"CONTAINER_20": Decimal("120000")}

    def get_effective_price(self, contract_id: str, service_id: str, business_date: date) -> Decimal:
        if contract_id == "no-price" or service_id not in self.prices:
            raise LookupError(f"No applicable price for service {service_id}")
        return self.prices[service_id]
