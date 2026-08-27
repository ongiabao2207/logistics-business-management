from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class ProductionRecord:
    service_id: str
    description: str
    quantity: Decimal
    period_start: date
    period_end: date
    status: str


class ProductionClient(Protocol):
    def get_eligible_records(self, contract_id: str, period_start: date, period_end: date) -> list[ProductionRecord]: ...


class FakeProductionClient:
    def get_eligible_records(self, contract_id: str, period_start: date, period_end: date) -> list[ProductionRecord]:
        if contract_id == "no-production":
            return []
        status = "PENDING" if contract_id == "unconfirmed-production" else "CONFIRMED"
        return [ProductionRecord("CONTAINER_20", "20-foot container handling", Decimal("12"), period_start, period_end, status)]
