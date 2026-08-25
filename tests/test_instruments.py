from tests.conftest import get_auth_header
from models.instrument import InstrumentStatus


def test_create_instrument(client, owner_user):
    headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    payload = {
        "instrument_id": "INST-TEST-001",
        "instrument_type": "Weighing Scale",
        "manufacturer": "Test Mfg",
        "model_number": "TM-100",
        "serial_number": "SN-TEST-001",
        "capacity": "50kg",
        "accuracy_class": "Class I",
        "location": "Mumbai",
    }
    r = client.post("/api/instruments/", json=payload, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["instrument_id"] == "INST-TEST-001"
    assert data["status"] == "REGISTERED"


def test_create_instrument_duplicate(client, owner_user):
    headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    payload = {
        "instrument_id": "INST-DUP-001",
        "instrument_type": "Scale",
        "serial_number": "SN-DUP-001",
    }
    r = client.post("/api/instruments/", json=payload, headers=headers)
    assert r.status_code == 200

    payload["serial_number"] = "SN-DUP-002"
    r = client.post("/api/instruments/", json=payload, headers=headers)
    assert r.status_code == 409


def test_create_instrument_admin_forbidden(client, admin_user):
    headers = get_auth_header(client, "testadmin@test.com", "adminpass")
    payload = {
        "instrument_id": "INST-ADM-001",
        "instrument_type": "Scale",
        "serial_number": "SN-ADM-001",
    }
    r = client.post("/api/instruments/", json=payload, headers=headers)
    assert r.status_code == 403


def test_list_instruments_owner_sees_own(client, owner_user):
    headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    client.post(
        "/api/instruments/",
        json={
            "instrument_id": "INST-OWN-001",
            "instrument_type": "Scale",
            "serial_number": "SN-OWN-001",
        },
        headers=headers,
    )
    r = client.get("/api/instruments/", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_list_instruments_admin_sees_all(client, admin_user, owner_user):
    owner_headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    client.post(
        "/api/instruments/",
        json={
            "instrument_id": "INST-ALL-001",
            "instrument_type": "Scale",
            "serial_number": "SN-ALL-001",
        },
        headers=owner_headers,
    )
    admin_headers = get_auth_header(client, "testadmin@test.com", "adminpass")
    r = client.get("/api/instruments/", headers=admin_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_get_instrument_by_id(client, owner_user):
    headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    r = client.post(
        "/api/instruments/",
        json={
            "instrument_id": "INST-GET-001",
            "instrument_type": "Scale",
            "serial_number": "SN-GET-001",
        },
        headers=headers,
    )
    inst_id = r.json()["id"]
    r = client.get(f"/api/instruments/{inst_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["instrument_id"] == "INST-GET-001"


def test_update_instrument(client, owner_user):
    headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    r = client.post(
        "/api/instruments/",
        json={
            "instrument_id": "INST-UPD-001",
            "instrument_type": "Scale",
            "serial_number": "SN-UPD-001",
        },
        headers=headers,
    )
    inst_id = r.json()["id"]
    r = client.put(
        f"/api/instruments/{inst_id}",
        json={"location": "Chennai"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["location"] == "Chennai"


def test_delete_instrument(client, owner_user):
    headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    r = client.post(
        "/api/instruments/",
        json={
            "instrument_id": "INST-DEL-001",
            "instrument_type": "Scale",
            "serial_number": "SN-DEL-001",
        },
        headers=headers,
    )
    inst_id = r.json()["id"]
    r = client.delete(f"/api/instruments/{inst_id}", headers=headers)
    assert r.status_code == 200
