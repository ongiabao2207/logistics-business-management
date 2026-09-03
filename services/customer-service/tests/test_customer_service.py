import pytest

from app.services.customer_service import CustomerService, CustomerServiceError


def test_list_customers_returns_database_rows(db, customer_factory):
    customer_factory()
    service = CustomerService()

    customers = service.list_customers(db, offset=0, limit=100)

    assert len(customers) == 1
    assert customers[0].id == "KH0001"
    assert customers[0].company_name == "Samsung Electronics HCMC"


def test_get_customer_returns_database_row(db, customer_factory):
    customer_factory()
    service = CustomerService()

    customer = service.get_customer(db, "KH0001")

    assert customer.id == "KH0001"
    assert customer.contact_name == "Nguyen Van An"


def test_get_customer_returns_not_found_for_unknown_customer(db):
    service = CustomerService()

    with pytest.raises(CustomerServiceError) as exc:
        service.get_customer(db, "KH9999")

    assert exc.value.status_code == 404
    assert exc.value.detail == "customer does not exist"
