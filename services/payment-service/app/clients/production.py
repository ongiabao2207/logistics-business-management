from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol

import httpx


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


class HttpProductionClient:
    def __init__(self, base_url: str, access_token: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {access_token}"}
        self.timeout = timeout

    def get_eligible_records(self, contract_id: str, period_start: date, period_end: date) -> list[ProductionRecord]:
        try:
            response = httpx.get(
                f"{self.base_url}/production-periods",
                params={"contract_id": contract_id},
                headers=self.headers,
                timeout=self.timeout,
            )
        except httpx.RequestError as exc:
            raise ConnectionError("Không thể kết nối Production Service") from exc
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ConnectionError(f"Production Service trả về lỗi HTTP {response.status_code}") from exc

        records: list[ProductionRecord] = []
        status_map = {"LOCKED": "CONFIRMED", "APPROVED": "RECONCILED"}
        for period in response.json():
            start = date.fromisoformat(period["from_date"])
            end = date.fromisoformat(period["to_date"])
            if start < period_start or end > period_end:
                continue
            mapped_status = status_map.get(period["status"], period["status"])
            for detail in period.get("details", []):
                records.append(
                    ProductionRecord(
                        service_id=str(detail["service_code"]),
                        description=detail.get("notes") or f"Dịch vụ {detail['service_code']}",
                        quantity=Decimal(str(detail["quantity"])),
                        period_start=start,
                        period_end=end,
                        status=mapped_status,
                    )
                )
        return records
