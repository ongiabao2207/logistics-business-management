from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CustomerInfo:
    id: str
    active: bool


class CustomerClient(Protocol):
    def get_customer(self, customer_id: str) -> CustomerInfo | None:
        ...


class FakeCustomerClient:
    _customers = {
        "customer-active": CustomerInfo(id="customer-active", active=True),
        "customer-inactive": CustomerInfo(id="customer-inactive", active=False),
    }

    def get_customer(self, customer_id: str) -> CustomerInfo | None:
        if customer_id in self._customers:
            return self._customers[customer_id]

        if customer_id.startswith("missing"):
            return None

        return CustomerInfo(id=customer_id, active=True)


def get_customer_client() -> CustomerClient:
    return FakeCustomerClient()
