from dataclasses import dataclass
from datetime import date
from typing import Protocol

import httpx


@dataclass(frozen=True)
class ContractSnapshot:
    id: str
    customer_id: str
    valid_from: date
    valid_to: date
    status: str


class ContractClient(Protocol):
    def get_contract(self, contract_id: str, customer_id: str) -> ContractSnapshot: ...


class FakeContractClient:
    def get_contract(self, contract_id: str, customer_id: str) -> ContractSnapshot:
        if contract_id == "missing-contract":
            raise LookupError("Contract was not found")
        if contract_id == "expired-contract":
            return ContractSnapshot(contract_id, customer_id, date(2020, 1, 1), date(2020, 12, 31), "ACTIVE")
        return ContractSnapshot(contract_id, customer_id, date(2020, 1, 1), date(2099, 12, 31), "ACTIVE")


class HttpContractClient:
    def __init__(self, base_url: str, access_token: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {access_token}"}
        self.timeout = timeout

    def get_contract(self, contract_id: str, customer_id: str) -> ContractSnapshot:
        try:
            response = httpx.get(
                f"{self.base_url}/contracts/{contract_id}",
                headers=self.headers,
                timeout=self.timeout,
            )
        except httpx.RequestError as exc:
            raise ConnectionError("Không thể kết nối Contract Service") from exc
        if response.status_code == 404:
            raise LookupError("Không tìm thấy hợp đồng")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ConnectionError(f"Contract Service trả về lỗi HTTP {response.status_code}") from exc
        data = response.json()
        upstream_customer_id = data.get("customer_id")
        if upstream_customer_id is not None and upstream_customer_id != customer_id:
            raise LookupError("Hợp đồng không thuộc khách hàng đã chọn")
        return ContractSnapshot(
            id=data.get("contract_id", contract_id),
            customer_id=upstream_customer_id or customer_id,
            valid_from=date.fromisoformat(data["valid_from"]),
            valid_to=date.fromisoformat(data["valid_to"]),
            status=data["status"],
        )
