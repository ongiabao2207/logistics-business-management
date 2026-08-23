BASE = "/api/v1/payments"


def payload(contract_id="contract-001"):
    return {
        "customer_id": "customer-001",
        "contract_id": contract_id,
        "period_start": "2026-08-01",
        "period_end": "2026-08-31",
        "tax_rate": "0.10",
    }


def test_payment_api_happy_path(client):
    preview = client.post(f"{BASE}/preview", json=payload())
    assert preview.status_code == 200
    assert preview.json()["total_amount"] == "1584000.00"

    created = client.post(BASE, json=payload())
    assert created.status_code == 201
    payment_id = created.json()["id"]
    assert created.json()["lines"][0]["unit_price_snapshot"] == "120000.00"

    fetched = client.get(f"{BASE}/{payment_id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == payment_id

    submitted = client.post(f"{BASE}/{payment_id}/submit")
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "PENDING_APPROVAL"


def test_adjustment_api_preserves_original_payment(client):
    payment = client.post(BASE, json=payload()).json()
    response = client.post(
        f"{BASE}/{payment['id']}/adjustments",
        json={"reason": "Correct handling surcharge", "amount": "25000"},
    )

    assert response.status_code == 201
    assert response.json()["amount"] == "25000.00"
    fetched = client.get(f"{BASE}/{payment['id']}").json()
    assert fetched["total_amount"] == payment["total_amount"]
    assert len(fetched["adjustments"]) == 1


def test_invalid_contract_period_returns_business_error(client):
    response = client.post(f"{BASE}/preview", json=payload("expired-contract"))

    assert response.status_code == 422
    assert "not valid" in response.json()["detail"]


def test_request_validation_rejects_reversed_period(client):
    body = payload()
    body["period_start"] = "2026-09-01"
    response = client.post(f"{BASE}/preview", json=body)

    assert response.status_code == 422
