from tests.conftest import get_auth_header
from models.instrument import InstrumentStatus
from passlib.context import CryptContext
from tests.conftest import TestSessionLocal
from models.user import User, UserRole


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


def test_owner_cannot_view_other_owner_instrument(client, owner_user):
    headers1 = get_auth_header(client, "testowner@test.com", "ownerpass")
    inst = client.post(
        "/api/instruments/",
        json={
            "instrument_id": "INST-XOWN-001",
            "instrument_type": "Scale",
            "serial_number": "SN-XOWN-001",
        },
        headers=headers1,
    ).json()

    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    db = TestSessionLocal()
    other = User(
        full_name="Other Owner", email="otherowner2@test.com", phone="8888888881",
        hashed_password=pwd.hash("pass"[:72]), role=UserRole.OWNER,
    )
    db.add(other)
    db.commit()
    db.close()

    headers2 = get_auth_header(client, "otherowner2@test.com", "pass")
    r = client.get(f"/api/instruments/{inst['id']}", headers=headers2)
    assert r.status_code == 403


def test_owner_cannot_update_other_owner_instrument(client, owner_user):
    headers1 = get_auth_header(client, "testowner@test.com", "ownerpass")
    inst = client.post(
        "/api/instruments/",
        json={
            "instrument_id": "INST-XOWN-002",
            "instrument_type": "Scale",
            "serial_number": "SN-XOWN-002",
        },
        headers=headers1,
    ).json()

    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    db = TestSessionLocal()
    other = User(
        full_name="Other Owner 3", email="otherowner3@test.com", phone="8888888882",
        hashed_password=pwd.hash("pass"[:72]), role=UserRole.OWNER,
    )
    db.add(other)
    db.commit()
    db.close()

    headers2 = get_auth_header(client, "otherowner3@test.com", "pass")
    r = client.put(f"/api/instruments/{inst['id']}", json={"location": "Hacked"}, headers=headers2)
    assert r.status_code == 403


def test_unauthenticated_instrument_access(client):
    r = client.get("/api/instruments/")
    assert r.status_code == 401


def test_inspector_cannot_create_instrument(client, inspector_user):
    headers = get_auth_header(client, "testinspector@test.com", "inspectorpass")
    r = client.post(
        "/api/instruments/",
        json={
            "instrument_id": "INST-INS-001",
            "instrument_type": "Scale",
            "serial_number": "SN-INS-001",
        },
        headers=headers,
    )
    assert r.status_code == 403
