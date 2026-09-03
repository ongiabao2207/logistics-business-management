def test_health(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "customer-service"}


def test_get_customers_returns_customer_list(client, customer_factory):
    customer_factory()

    response = client.get("/api/v1/customers")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == "KH0001"
    assert body[0]["company_name"] == "Samsung Electronics HCMC"
    assert body[0]["company_type"] == "Logistics"
    assert body[0]["tax_code"] == "0312345678"
    assert body[0]["status"] == "ACTIVE"


def test_get_customer_returns_customer_detail(client, customer_factory):
    customer_factory()

    response = client.get("/api/v1/customers/KH0001")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "KH0001"
    assert body["contact_name"] == "Nguyen Van An"
    assert body["contact_email"] == "an.nguyen@samsung.example"
    assert body["contact_phone"] == "0901234567"


def test_get_customer_returns_not_found_for_unknown_customer(client):
    response = client.get("/api/v1/customers/KH9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "customer does not exist"
