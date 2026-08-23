def create_price_list(client, service_id, version=1):
    response = client.post(
        "/price-lists",
        json={
            "description": f"Bảng giá phiên bản {version}",
            "version": version,
            "effective_from": "2026-01-01",
            "effective_to": "2026-12-31",
            "details": [{"service_id": service_id, "unit_price": "120000.00"}],
        },
    )
    assert response.status_code == 201
    return response.json()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "price-service"}


def test_create_list_and_deactivate_service(client):
    create_response = client.post(
        "/services",
        json={
            "name": "Bốc xếp Container",
            "description": "Dịch vụ bốc xếp",
            "unit": "Container",
        },
    )
    assert create_response.status_code == 201
    service_id = create_response.json()["id"]

    list_response = client.get("/services")
    assert list_response.status_code == 200
    assert list_response.json()[0]["is_active"] is True

    delete_response = client.delete(f"/services/{service_id}")
    assert delete_response.status_code == 204

    updated_list = client.get("/services")
    assert updated_list.json()[0]["is_active"] is False


def test_create_and_list_price_lists(client, service_factory):
    service = service_factory()
    created = create_price_list(client, service.id)

    detail_response = client.get(f"/price-lists/{created['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["status"] == "DRAFT"

    list_response = client.get("/price-lists")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_create_price_list_rejects_duplicate_service(client, service_factory):
    service = service_factory()
    response = client.post(
        "/price-lists",
        json={
            "description": "Bảng giá lỗi",
            "version": 1,
            "effective_from": "2026-01-01",
            "effective_to": "2026-12-31",
            "details": [
                {"service_id": service.id, "unit_price": "1.00"},
                {"service_id": service.id, "unit_price": "2.00"},
            ],
        },
    )
    assert response.status_code == 422


def test_submit_draft_price_list(client, service_factory):
    service = service_factory()
    price_list = create_price_list(client, service.id)

    response = client.post(f"/price-lists/{price_list['id']}/submit")

    assert response.status_code == 200
    assert response.json()["status"] == "SUBMITTED"


def test_update_and_delete_are_limited_to_draft(client, service_factory):
    service = service_factory()
    draft = create_price_list(client, service.id)

    update_response = client.patch(
        f"/price-lists/{draft['id']}", json={"description": "Bảng giá đã sửa"}
    )
    assert update_response.status_code == 200

    client.post(f"/price-lists/{draft['id']}/submit")
    blocked_update = client.patch(
        f"/price-lists/{draft['id']}", json={"description": "Không được sửa"}
    )
    blocked_delete = client.delete(f"/price-lists/{draft['id']}")
    assert blocked_update.status_code == 409
    assert blocked_delete.status_code == 409

    deletable = create_price_list(client, service.id, version=2)
    delete_response = client.delete(f"/price-lists/{deletable['id']}")
    assert delete_response.status_code == 204
    assert client.get(f"/price-lists/{deletable['id']}").status_code == 404


def test_get_active_service_price(
    client, service_factory, set_price_list_status
):
    service = service_factory()
    price_list = create_price_list(client, service.id)
    set_price_list_status(price_list["id"], "ACTIVE")

    response = client.get(f"/price-lists/active/services/{service.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["service_name"] == "Lưu kho"
    assert body["unit_price"] == "120000.00"
    assert body["version"] == 1


def test_delete_unknown_service_returns_not_found(client):
    assert client.delete("/services/999").status_code == 404
