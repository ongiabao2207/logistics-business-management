from app.models.payment_model import Payment, PaymentStatus


BASE = "/api/v1/payments"


def payload(contract_id: str = "contract-001") -> dict:
    return {
        "customer_id": "customer-001",
        "contract_id": contract_id,
        "period_start": "2026-08-01",
        "period_end": "2026-08-31",
        "tax_rate": "0.10",
    }


def test_payment_api_happy_path(client):
    preview_response = client.post(
        f"{BASE}/preview",
        json=payload(),
    )

    assert preview_response.status_code == 200
    assert (
        preview_response.json()["total_amount"]
            == "1584000"
    )

    create_response = client.post(
        BASE,
        json=payload(),
    )

    assert create_response.status_code == 201

    payment_data = create_response.json()
    payment_id = payment_data["id"]

    assert (
        payment_data["lines"][0][
            "unit_price_snapshot"
        ]
        == "120000"
    )

    get_response = client.get(
        f"{BASE}/{payment_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == payment_id

    submit_response = client.post(
        f"{BASE}/{payment_id}/submit"
    )

    assert submit_response.status_code == 200
    assert (
        submit_response.json()["status"]
        == "PENDING_APPROVAL"
    )


def test_list_payments_returns_newest_payment_first(client):
    first = client.post(BASE, json=payload("contract-list-first"))
    second = client.post(BASE, json=payload("contract-list-second"))

    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(BASE)

    assert response.status_code == 200
    payment_ids = [payment["id"] for payment in response.json()]
    assert payment_ids.index(second.json()["id"]) < payment_ids.index(first.json()["id"])


def test_create_payment_rejects_accountant_billing_quantity(client):
    create_payload = payload("contract-create-adjusted")
    create_payload["lines"] = [
        {"service_id": "CONTAINER_20", "billing_quantity": 10}
    ]

    response = client.post(BASE, json=create_payload)

    assert response.status_code == 422


def test_accountant_applies_approval_revision_request(client, db_session):
    create_response = client.post(
        BASE,
        json=payload(),
    )

    assert create_response.status_code == 201

    payment_id = create_response.json()["id"]
    payment = db_session.get(Payment, payment_id)
    payment.status = PaymentStatus.REVISION_REQUESTED
    db_session.commit()

    adjustment_response = client.post(
        f"{BASE}/{payment_id}/adjustments",
        json={
            "revision_request_id": "approval-revision-001",
            "adjustment_note": "Correct the tax rate",
            "tax_rate": "0.08",
        },
    )

    assert adjustment_response.status_code == 201
    adjusted = adjustment_response.json()
    assert adjusted["status"] == "PENDING_APPROVAL"
    assert adjusted["lines"][0]["confirmed_quantity"] == "12"
    assert adjusted["lines"][0]["billing_quantity"] == "12"
    assert adjusted["lines"][0]["tax_rate"] == "0.08"
    assert adjusted["total_amount"] == "1555200"
    assert adjusted["adjustments"][0]["revision_request_id"] == "approval-revision-001"
    assert adjusted["adjustments"][0]["adjustment_note"] == "Correct the tax rate"
    assert adjusted["adjustments"][0]["change_type"] == "REVISION_ADJUSTMENT"

    get_response = client.get(
        f"{BASE}/{payment_id}"
    )

    assert get_response.status_code == 200

    assert get_response.json()["status"] == "PENDING_APPROVAL"
    assert get_response.json()["total_amount"] == "1555200"

    duplicate_response = client.post(
        f"{BASE}/{payment_id}/adjustments",
        json={
            "revision_request_id": "approval-revision-001",
            "adjustment_note": "Attempt to apply the same request twice",
            "tax_rate": "0.07",
        },
    )
    assert duplicate_response.status_code == 409


def test_adjustment_rejects_draft_payment(client):
    create_response = client.post(BASE, json=payload())
    payment_id = create_response.json()["id"]

    response = client.post(
        f"{BASE}/{payment_id}/adjustments",
        json={
            "revision_request_id": "approval-revision-002",
            "adjustment_note": "Payment has not been returned by approval",
            "tax_rate": "0.08",
        },
    )

    assert response.status_code == 409


def test_adjustment_rejects_approval_request_fields(client, db_session):
    create_response = client.post(BASE, json=payload())
    payment_id = create_response.json()["id"]
    payment = db_session.get(Payment, payment_id)
    payment.status = PaymentStatus.REVISION_REQUESTED
    db_session.commit()

    response = client.post(
        f"{BASE}/{payment_id}/adjustments",
        json={
            "reason_code": "PAYMENT_INFORMATION_INCORRECT",
            "detail": "These fields belong to Approval Service",
            "lines": [
                {
                    "service_id": "CONTAINER_20",
                    "billing_quantity": 10,
                }
            ],
        },
    )

    assert response.status_code == 422


def test_invalid_contract_period_returns_business_error(
    client,
):
    response = client.post(
        f"{BASE}/preview",
        json=payload("expired-contract"),
    )

    assert response.status_code == 422
    assert "not valid" in response.json()["detail"]


def test_request_validation_rejects_reversed_period(
    client,
):
    request_body = payload()
    request_body["period_start"] = "2026-09-01"

    response = client.post(
        f"{BASE}/preview",
        json=request_body,
    )

    assert response.status_code == 422


def test_create_payment_rejects_duplicate(client):
    first_response = client.post(
        BASE,
        json=payload(),
    )

    second_response = client.post(
        BASE,
        json=payload(),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert (
        "already exists"
        in second_response.json()["detail"]
    )


def test_update_draft_changes_tax_and_keeps_confirmed_quantity(client):
    create_response = client.post(BASE, json=payload())
    assert create_response.status_code == 201
    payment_id = create_response.json()["id"]

    update_response = client.patch(
        f"{BASE}/{payment_id}",
        json={
            "reason": "Correct tax rate",
            "tax_rate": "0.08",
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["status"] == "DRAFT"
    assert updated["lines"][0]["confirmed_quantity"] == "12"
    assert updated["lines"][0]["billing_quantity"] == "12"
    assert updated["lines"][0]["unit_price_snapshot"] == "120000"
    assert updated["subtotal"] == "1440000"
    assert updated["tax_amount"] == "115200"
    assert updated["total_amount"] == "1555200"
    assert updated["adjustments"][0]["change_type"] == "DRAFT_EDIT"
    assert updated["adjustments"][0]["action"] == "UPDATE"


def test_submitted_payment_cannot_be_updated(client):
    create_response = client.post(BASE, json=payload())
    payment_id = create_response.json()["id"]
    submit_response = client.post(f"{BASE}/{payment_id}/submit")
    assert submit_response.status_code == 200

    update_response = client.patch(
        f"{BASE}/{payment_id}",
        json={"reason": "Correct tax rate", "tax_rate": "0.08"},
    )

    assert update_response.status_code == 409
    assert "cannot be edited" in update_response.json()["detail"]


def test_update_rejects_billing_quantity(client):
    create_response = client.post(BASE, json=payload())
    payment_id = create_response.json()["id"]

    response = client.patch(
        f"{BASE}/{payment_id}",
        json={
            "reason": "Attempt to edit confirmed production",
            "tax_rate": "0.08",
            "lines": [
                {
                    "service_id": "CONTAINER_20",
                    "billing_quantity": "13",
                }
            ],
        },
    )

    assert response.status_code == 422


def test_update_rejects_original_quantity_and_description_fields(client):
    create_response = client.post(BASE, json=payload())
    payment_id = create_response.json()["id"]

    response = client.patch(
        f"{BASE}/{payment_id}",
        json={
            "reason": "Attempt to edit source production",
            "lines": [
                {
                    "service_id": "CONTAINER_20",
                    "billing_quantity": "10",
                    "quantity": "10",
                    "description": "Changed by frontend",
                }
            ],
        },
    )

    assert response.status_code == 422


def test_update_requires_adjustment_reason(client):
    create_response = client.post(BASE, json=payload())
    payment_id = create_response.json()["id"]

    response = client.patch(
        f"{BASE}/{payment_id}",
        json={"tax_rate": "0.08"},
    )

    assert response.status_code == 422
