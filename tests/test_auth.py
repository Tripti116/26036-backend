from tests.conftest import get_auth_header


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_register_user(client):
    payload = {
        "full_name": "New User",
        "email": "new@test.com",
        "phone": "5555555555",
        "password": "pass123",
        "role": "OWNER",
        "organization": "Org",
        "address": "Addr",
    }
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "new@test.com"
    assert data["role"] == "OWNER"
    assert "hashed_password" not in data


def test_register_duplicate_email(client):
    payload = {
        "full_name": "User1",
        "email": "dup@test.com",
        "phone": "6000000001",
        "password": "pass123",
        "role": "OWNER",
    }
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 200

    payload["full_name"] = "User2"
    payload["phone"] = "6000000002"
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 409


def test_login_success(client):
    payload = {
        "full_name": "Login User",
        "email": "login@test.com",
        "phone": "7000000001",
        "password": "mypassword",
        "role": "INSPECTOR",
    }
    client.post("/api/auth/register", json=payload)

    r = client.post(
        "/api/auth/login",
        data={"username": "login@test.com", "password": "mypassword"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password(client):
    payload = {
        "full_name": "Wrong Pass User",
        "email": "wrongpass@test.com",
        "phone": "7000000002",
        "password": "correctpass",
        "role": "OWNER",
    }
    client.post("/api/auth/register", json=payload)

    r = client.post(
        "/api/auth/login",
        data={"username": "wrongpass@test.com", "password": "wrongpass"},
    )
    assert r.status_code == 401


def test_login_nonexistent_user(client):
    r = client.post(
        "/api/auth/login",
        data={"username": "nonexistent@test.com", "password": "pass"},
    )
    assert r.status_code == 401


def test_get_me(client, owner_user):
    headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "testowner@test.com"
    assert r.json()["role"] == "OWNER"


def test_get_me_no_token(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_demo_admin_login(client, seed_demo_accounts):
    r = client.post(
        "/api/auth/login",
        data={"username": "admin@sih.com", "password": "admin123"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_demo_inspector_login(client, seed_demo_accounts):
    r = client.post(
        "/api/auth/login",
        data={"username": "inspector@sih.com", "password": "inspector123"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_demo_owner_login(client, seed_demo_accounts):
    r = client.post(
        "/api/auth/login",
        data={"username": "owner@sih.com", "password": "owner123"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()
