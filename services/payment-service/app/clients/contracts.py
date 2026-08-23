from dataclasses import dataclass
from datetime import date
from typing import Protocol


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
