import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

def test_register_and_login():
    payload = {
        "full_name": "Test User",
        "email": "test@example.com",
        "phone": "1234567890",
        "password": "testpass",
        "role": "OWNER",
        "organization": "DemoOrg",
        "address": "DemoAddress"
    }
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 200
    r = client.post("/api/auth/login", data={"username": "test@example.com", "password": "testpass"})
    assert r.status_code == 200
    assert "access_token" in r.json()
