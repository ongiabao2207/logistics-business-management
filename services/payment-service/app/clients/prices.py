from datetime import date
from decimal import Decimal
from typing import Protocol

import httpx


class PriceClient(Protocol):
    def get_effective_price(self, contract_id: str, service_id: str, business_date: date) -> Decimal: ...


class FakePriceClient:
    prices = {"CONTAINER_20": Decimal("120000")}

    def get_effective_price(self, contract_id: str, service_id: str, business_date: date) -> Decimal:
        if contract_id == "no-price" or service_id not in self.prices:
            raise LookupError(f"No applicable price for service {service_id}")
        return self.prices[service_id]


class HttpPriceClient:
    def __init__(self, base_url: str, access_token: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {access_token}"}
        self.timeout = timeout

    def get_effective_price(self, contract_id: str, service_id: str, business_date: date) -> Decimal:
        try:
            numeric_service_id = int(service_id)
        except ValueError as exc:
            raise LookupError(f"Mã dịch vụ Price không hợp lệ: {service_id}") from exc
        try:
            response = httpx.get(
                f"{self.base_url}/price-lists",
                params={"limit": 500},
                headers=self.headers,
                timeout=self.timeout,
            )
        except httpx.RequestError as exc:
            raise ConnectionError("Không thể kết nối Price Service") from exc
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ConnectionError(f"Price Service trả về lỗi HTTP {response.status_code}") from exc

        for price_list in response.json():
            if (
                price_list["status"] == "EFFECTIVE"
                and date.fromisoformat(price_list["effective_from"]) <= business_date
                and date.fromisoformat(price_list["effective_to"]) >= business_date
            ):
                for detail in price_list.get("details", []):
                    if detail["service_id"] == numeric_service_id:
                        return Decimal(str(detail["unit_price"]))
        raise LookupError(f"Không có đơn giá phù hợp cho dịch vụ {service_id}")
