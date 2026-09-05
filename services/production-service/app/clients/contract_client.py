from dataclasses import dataclass
from datetime import date
from typing import Protocol

import httpx


@dataclass(frozen=True)
class ContractValidation:
    customer_id: str
    allowed_service_codes: set[str]


class ContractClient(Protocol):
    def validate_production_period(self, contract_id: str, from_date: date, to_date: date) -> ContractValidation: ...


class HttpContractClient:
    """Adapter for the planned public Contract Service validation endpoint."""

    def __init__(self, base_url: str, access_token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token

    def validate_production_period(self, contract_id: str, from_date: date, to_date: date) -> ContractValidation:
        try:
            response = httpx.get(
                f"{self.base_url}/api/v1/contracts/{contract_id}/validate-services",
                params={"fromDate": from_date.isoformat(), "toDate": to_date.isoformat()},
                headers={"Authorization": f"Bearer {self.access_token}"} if self.access_token else None,
                timeout=5.0,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.json().get("detail", "Contract validation failed")
            raise ValueError(detail) from exc
        except httpx.RequestError as exc:
            raise ValueError("Contract service is unavailable") from exc
        data = response.json()
        return ContractValidation(customer_id=data["customer_id"], allowed_service_codes=set(data["service_codes"]))


class FakeContractClient:
    """Deterministic development substitute until Contract Service exposes its API."""

    def validate_production_period(self, contract_id: str, from_date: date, to_date: date) -> ContractValidation:
        seed_customers = {
            "HD-2024-TCB-082": "KH-TCB-001",
            "CONT-2023-GT-01": "KH-GTECH-002",
            "HD-VIG-2024-012": "KH-VIG-003",
            "HD-2023-VOS-001": "KH-VOS-004",
            "HD-SHO-2024-LGT": "KH-SHO-005",
        }
        customer_id = seed_customers.get(contract_id)
        if customer_id is None:
            raise ValueError("Contract is not available in the development seed data")
        return ContractValidation(
            customer_id=customer_id,
            allowed_service_codes={"LOADING", "STORAGE", "TRANSPORT", "SRV-BX-20FT", "SRV-BX-40FT", "SRV-STORAGE", "SRV-TRANSPORT", "SRV-COUNT", "SRV-LIFT"},
        )
