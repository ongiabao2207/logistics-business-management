from datetime import date, datetime, timedelta, timezone


def create_price_list(
    client,
    service_id,
    description="Bảng giá dùng cho kiểm thử",
    effective_from="2026-01-01",
    effective_to="2026-12-31",
):
    response = client.post(
        "/api/v1/price-lists",
        json={
            "description": description,
            "effective_from": effective_from,
            "effective_to": effective_to,
            "details": [{"service_id": service_id, "unit_price": "120000.00"}],
        },
    )
    assert response.status_code == 201
    body = response.json()
    year = datetime.now(timezone.utc).year
    assert body["id"].startswith(f"BG-{year}-")
    return body


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "price-service"}


def test_create_list_and_deactivate_service(client):
    create_response = client.post(
        "/api/v1/services",
        json={
            "name": "Bốc xếp Container",
            "description": "Dịch vụ bốc xếp",
            "unit": "Container",
        },
    )
    assert create_response.status_code == 201
    service_id = create_response.json()["id"]

    list_response = client.get("/api/v1/services")
    assert list_response.status_code == 200
    assert list_response.json()[0]["is_active"] is True

    delete_response = client.delete(f"/api/v1/services/{service_id}")
    assert delete_response.status_code == 204

    updated_list = client.get("/api/v1/services")
    assert updated_list.json()[0]["is_active"] is False


def test_service_active_status_is_generated_by_system(client):
    response = client.post(
        "/api/v1/services",
        json={
            "name": "Van chuyen noi bo",
            "description": "Dich vu van chuyen noi bo",
            "unit": "Chuyen",
        },
    )
    assert response.status_code == 201
    assert response.json()["is_active"] is True

    manual_status = client.post(
        "/api/v1/services",
        json={
            "name": "Van chuyen ngoai bo",
            "description": "Dich vu van chuyen ngoai bo",
            "unit": "Chuyen",
            "is_active": False,
        },
    )
    assert manual_status.status_code == 422


def test_create_and_list_price_lists(client, service_factory):
    service = service_factory()
    created = create_price_list(client, service.id)

    detail_response = client.get(f"/api/v1/price-lists/{created['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["status"] == "DRAFT"

    list_response = client.get("/api/v1/price-lists")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_create_price_list_rejects_duplicate_service(client, service_factory):
    service = service_factory()
    response = client.post(
        "/api/v1/price-lists",
        json={
            "description": "Bảng giá lỗi",
            "effective_from": "2026-01-01",
            "effective_to": "2026-12-31",
            "details": [
                {"service_id": service.id, "unit_price": "1.00"},
                {"service_id": service.id, "unit_price": "2.00"},
            ],
        },
    )
    assert response.status_code == 422


def test_create_price_list_rejects_duplicate_description(client, service_factory):
    service = service_factory()
    create_price_list(client, service.id, "Bang gia tieu chuan")

    response = client.post(
        "/api/v1/price-lists",
        json={
            "description": "  BANG GIA TIEU CHUAN  ",
            "effective_from": "2027-01-01",
            "effective_to": "2027-12-31",
            "details": [{"service_id": service.id, "unit_price": "130000.00"}],
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Price list description already exists"


def test_submit_draft_price_list(client, service_factory):
    service = service_factory()
    price_list = create_price_list(client, service.id)

    response = client.post(f"/api/v1/price-lists/{price_list['id']}/submit")

    assert response.status_code == 200
    assert response.json()["status"] == "SUBMITTED"


def test_approval_rejects_overlapping_effective_period(client, service_factory):
    service = service_factory()
    today = date.today()
    first = create_price_list(
        client,
        service.id,
        "Bang gia dot mot",
        (today + timedelta(days=10)).isoformat(),
        (today + timedelta(days=30)).isoformat(),
    )
    overlapping = create_price_list(
        client,
        service.id,
        "Bang gia bi chong",
        (today + timedelta(days=20)).isoformat(),
        (today + timedelta(days=40)).isoformat(),
    )
    assert client.post(f"/api/v1/price-lists/{first['id']}/submit").status_code == 200
    assert client.post(f"/api/v1/price-lists/{overlapping['id']}/submit").status_code == 200
    assert client.post(f"/api/v1/price-lists/{first['id']}/approve").status_code == 200

    response = client.post(f"/api/v1/price-lists/{overlapping['id']}/approve")

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Price list effective period overlaps an approved price list"
    )


def test_approval_allows_non_overlapping_effective_period(client, service_factory):
    service = service_factory()
    today = date.today()
    first = create_price_list(
        client,
        service.id,
        "Bang gia dot mot",
        (today + timedelta(days=10)).isoformat(),
        (today + timedelta(days=20)).isoformat(),
    )
    next_period = create_price_list(
        client,
        service.id,
        "Bang gia dot hai",
        (today + timedelta(days=21)).isoformat(),
        (today + timedelta(days=30)).isoformat(),
    )
    assert client.post(f"/api/v1/price-lists/{first['id']}/submit").status_code == 200
    assert client.post(f"/api/v1/price-lists/{next_period['id']}/submit").status_code == 200
    assert client.post(f"/api/v1/price-lists/{first['id']}/approve").status_code == 200

    response = client.post(f"/api/v1/price-lists/{next_period['id']}/approve")

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


def test_approve_current_price_list_makes_it_effective(client, service_factory):
    service = service_factory()
    today = date.today()
    price_list = create_price_list(
        client,
        service.id,
        "Bang gia ap dung ngay",
        (today - timedelta(days=1)).isoformat(),
        (today + timedelta(days=1)).isoformat(),
    )
    assert client.post(f"/api/v1/price-lists/{price_list['id']}/submit").status_code == 200

    response = client.post(f"/api/v1/price-lists/{price_list['id']}/approve")

    assert response.status_code == 200
    assert response.json()["status"] == "EFFECTIVE"


def test_approve_future_price_list_keeps_it_approved(client, service_factory):
    service = service_factory()
    today = date.today()
    price_list = create_price_list(
        client,
        service.id,
        "Bang gia tuong lai",
        (today + timedelta(days=1)).isoformat(),
        (today + timedelta(days=30)).isoformat(),
    )
    assert client.post(f"/api/v1/price-lists/{price_list['id']}/submit").status_code == 200

    response = client.post(f"/api/v1/price-lists/{price_list['id']}/approve")

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


def test_patch_rejected_price_list_returns_it_to_draft(client, service_factory):
    service = service_factory()
    price_list = create_price_list(client, service.id)
    assert client.post(f"/api/v1/price-lists/{price_list['id']}/submit").status_code == 200

    rejected = client.post(f"/api/v1/price-lists/{price_list['id']}/reject")
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "REJECTED"

    revised = client.patch(
        f"/api/v1/price-lists/{price_list['id']}",
        json={"description": "Bang gia da chinh sua sau khi tu choi"},
    )
    assert revised.status_code == 200
    assert revised.json()["status"] == "DRAFT"
    assert revised.json()["description"] == "Bang gia da chinh sua sau khi tu choi"


def test_new_effective_price_list_supersedes_old_one(
    client, service_factory, set_price_list_status
):
    service = service_factory()
    today = date.today()
    start = (today - timedelta(days=10)).isoformat()
    end = (today + timedelta(days=10)).isoformat()
    old = create_price_list(client, service.id, "Bang gia cu", start, end)
    set_price_list_status(old["id"], "EFFECTIVE")
    new = create_price_list(client, service.id, "Bang gia moi", start, end)
    assert client.post(f"/api/v1/price-lists/{new['id']}/submit").status_code == 200

    response = client.post(f"/api/v1/price-lists/{new['id']}/approve")

    assert response.status_code == 200
    assert response.json()["status"] == "EFFECTIVE"
    assert client.get(f"/api/v1/price-lists/{old['id']}").json()["status"] == "SUPERSEDED"


def test_status_sync_activates_due_approved_price_list(
    client, service_factory, set_price_list_status
):
    service = service_factory()
    today = date.today()
    price_list = create_price_list(
        client,
        service.id,
        "Bang gia da den ngay",
        (today - timedelta(days=1)).isoformat(),
        (today + timedelta(days=1)).isoformat(),
    )
    set_price_list_status(price_list["id"], "APPROVED")

    response = client.get(f"/api/v1/price-lists/{price_list['id']}")

    assert response.status_code == 200
    assert response.json()["status"] == "EFFECTIVE"


def test_status_sync_expires_elapsed_effective_price_list(
    client, service_factory, set_price_list_status
):
    service = service_factory()
    today = date.today()
    price_list = create_price_list(
        client,
        service.id,
        "Bang gia da het han",
        (today - timedelta(days=10)).isoformat(),
        (today - timedelta(days=1)).isoformat(),
    )
    set_price_list_status(price_list["id"], "EFFECTIVE")

    response = client.get(f"/api/v1/price-lists/{price_list['id']}")

    assert response.status_code == 200
    assert response.json()["status"] == "EXPIRED"


def test_update_and_delete_are_limited_to_draft(client, service_factory):
    service = service_factory()
    draft = create_price_list(client, service.id)

    update_response = client.patch(
        f"/api/v1/price-lists/{draft['id']}", json={"description": "Bảng giá đã sửa"}
    )
    assert update_response.status_code == 200

    client.post(f"/api/v1/price-lists/{draft['id']}/submit")
    blocked_update = client.patch(
        f"/api/v1/price-lists/{draft['id']}", json={"description": "Không được sửa"}
    )
    blocked_delete = client.delete(f"/api/v1/price-lists/{draft['id']}")
    assert blocked_update.status_code == 409
    assert blocked_delete.status_code == 409

    deletable = create_price_list(client, service.id, "Bảng giá có thể xóa")
    delete_response = client.delete(f"/api/v1/price-lists/{deletable['id']}")
    assert delete_response.status_code == 204
    assert client.get(f"/api/v1/price-lists/{deletable['id']}").status_code == 404


def test_update_price_list_rejects_duplicate_description(client, service_factory):
    service = service_factory()
    create_price_list(client, service.id, "Bang gia thu nhat")
    second = create_price_list(client, service.id, "Bang gia thu hai")

    response = client.patch(
        f"/api/v1/price-lists/{second['id']}",
        json={"description": " BANG GIA THU NHAT "},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Price list description already exists"


def test_get_effective_service_price(
    client, service_factory, set_price_list_status
):
    service = service_factory()
    price_list = create_price_list(client, service.id)
    set_price_list_status(price_list["id"], "EFFECTIVE")

    response = client.get(f"/api/v1/price-lists/effective/services/{service.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["service_name"] == "Lưu kho"
    assert body["unit_price"] == "120000.00"
    assert "version" not in body


def test_delete_unknown_service_returns_not_found(client):
    assert client.delete("/api/v1/services/999").status_code == 404
