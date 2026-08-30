def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_login_and_get_current_account(client, login):
    token = login()
    response = client.get("/api/v1/auth/me", headers=auth_header(token))

    assert response.status_code == 200
    assert response.json()["username"] == "admin"
    assert response.json()["role"]["name"] == "ROLE_ADMIN"
    assert "password_hash" not in response.json()


def test_login_rejects_bad_credentials(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_login_rejects_inactive_account(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "inactive_user", "password": "InactivePassword123!"},
    )
    assert response.status_code == 403


def test_non_admin_cannot_list_accounts(client, login):
    token = login("sale_user", "SalePassword123!")
    response = client.get("/api/v1/accounts", headers=auth_header(token))
    assert response.status_code == 403


def test_admin_creates_account_without_exposing_password_hash(client, login):
    token = login()
    roles = client.get("/api/v1/roles", headers=auth_header(token)).json()
    legal_role_id = next(role["id"] for role in roles if role["name"] == "ROLE_LEGAL")

    response = client.post(
        "/api/v1/accounts",
        headers=auth_header(token),
        json={
            "username": "legal_user",
            "email": "legal@abc.com",
            "password": "LegalPassword123!",
            "role_id": legal_role_id,
        },
    )

    assert response.status_code == 201
    assert response.json()["role"]["name"] == "ROLE_LEGAL"
    assert "password_hash" not in response.json()


def test_duplicate_username_is_rejected(client, login):
    token = login()
    response = client.post(
        "/api/v1/accounts",
        headers=auth_header(token),
        json={
            "username": "admin",
            "email": "another@abc.com",
            "password": "AnotherPassword123!",
            "role_id": 1,
        },
    )
    assert response.status_code == 409


def test_admin_cannot_deactivate_self(client, login):
    token = login()
    me = client.get("/api/v1/auth/me", headers=auth_header(token)).json()
    response = client.patch(
        f"/api/v1/accounts/{me['id']}/status",
        headers=auth_header(token),
        json={"is_active": False},
    )
    assert response.status_code == 400


def test_jwks_exposes_public_key(client):
    response = client.get("/.well-known/jwks.json")
    assert response.status_code == 200
    assert response.json()["keys"][0]["kid"] == "identity-key-1"
    assert "d" not in response.json()["keys"][0]
