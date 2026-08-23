from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CustomerInfo:
    id: str
    name: str
    tax_code: str
    customer_type: str
    status: str


class CustomerClient(Protocol):
    def get_customer(self, customer_id: str) -> CustomerInfo | None:
        ...


class FakeCustomerClient:
    _customers = {
        "KH0001": CustomerInfo(
            id="KH0001",
            name="Samsung Electronics HCMC",
            tax_code="0312345678",
            customer_type="Logistics",
            status="ACTIVE",
        ),
        "KH0002": CustomerInfo(
            id="KH0002",
            name="Vinamilk",
            tax_code="0300588569",
            customer_type="FMCG",
            status="ACTIVE",
        ),
        "KH0003": CustomerInfo(
            id="KH0003",
            name="Thaco Logistics",
            tax_code="4000123456",
            customer_type="Logistics",
            status="ACTIVE",
        ),
        "KH0004": CustomerInfo(
            id="KH0004",
            name="Nestle Viet Nam",
            tax_code="0302012345",
            customer_type="FMCG",
            status="ACTIVE",
        ),
        "KH0005": CustomerInfo(
            id="KH0005",
            name="Intel Products Vietnam",
            tax_code="0309876543",
            customer_type="Manufacturing",
            status="ACTIVE",
        ),
    }

    def get_customer(self, customer_id: str) -> CustomerInfo | None:
        return self._customers.get(customer_id)


def get_customer_client() -> CustomerClient:
    return FakeCustomerClient()
