from tests.conftest import get_auth_header
from datetime import datetime, timedelta, timezone
from models.instrument import Instrument


def _create_instrument(client, headers, instrument_id, serial_number):
    r = client.post(
        "/api/instruments/",
        json={
            "instrument_id": instrument_id,
            "instrument_type": "Weighing Scale",
            "manufacturer": "Test Mfg",
            "model_number": "M-300",
            "serial_number": serial_number,
            "capacity": "50kg",
        },
        headers=headers,
    )
    return r.json()


def _complete_verification(client, owner_headers, admin_headers, inspector_headers,
                           inspector_id, instrument, expected, measured, tolerance):
    client.post(
        "/api/verification/request",
        json={"instrument_id": instrument["id"]},
        headers=owner_headers,
    )
    r = client.get("/api/verification/", headers=admin_headers)
    pending = [v for v in r.json() if v["status"] == "PENDING"]
    vid = pending[-1]["id"]
    client.put(
        f"/api/verification/{vid}/assign",
        json={"inspector_id": inspector_id},
        headers=admin_headers,
    )
    client.put(
        f"/api/verification/{vid}/complete",
        json={
            "reference_standard_used": "NIST",
            "expected_value": expected,
            "measured_value": measured,
            "tolerance_limit": tolerance,
            "remarks": "Risk test",
        },
        headers=inspector_headers,
    )


def test_risk_score_new_instrument(client, owner_user):
    headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    inst = _create_instrument(client, headers, "INST-RISK-001", "SN-RISK-001")
    r = client.get(f"/api/instruments/{inst['id']}/risk", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["instrument_id"] == "INST-RISK-001"
    assert isinstance(data["risk_score"], int)
    assert 0 <= data["risk_score"] <= 100
    assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert isinstance(data["risk_factors"], list)


def test_risk_score_after_fail(client, owner_user, admin_user, inspector_user):
    owner_headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    admin_headers = get_auth_header(client, "testadmin@test.com", "adminpass")
    inspector_headers = get_auth_header(client, "testinspector@test.com", "inspectorpass")

    inst = _create_instrument(client, owner_headers, "INST-RISK-002", "SN-RISK-002")
    _complete_verification(
        client, owner_headers, admin_headers, inspector_headers,
        inspector_user.id, inst, 100.0, 110.0, 1.0,
    )

    r = client.get(f"/api/instruments/{inst['id']}/risk", headers=owner_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["risk_score"] > 0
    assert data["risk_level"] in ("MEDIUM", "HIGH")
    assert len(data["risk_factors"]) > 0


def test_risk_score_low_after_pass(client, owner_user, admin_user, inspector_user):
    owner_headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    admin_headers = get_auth_header(client, "testadmin@test.com", "adminpass")
    inspector_headers = get_auth_header(client, "testinspector@test.com", "inspectorpass")

    inst = _create_instrument(client, owner_headers, "INST-RISK-003", "SN-RISK-003")
    _complete_verification(
        client, owner_headers, admin_headers, inspector_headers,
        inspector_user.id, inst, 100.0, 100.1, 1.0,
    )

    r = client.get(f"/api/instruments/{inst['id']}/risk", headers=owner_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["risk_level"] == "LOW"
    assert data["risk_score"] < 30


def test_risk_unauthorized_other_owner(client, owner_user, admin_user, inspector_user):
    owner_headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    inst = _create_instrument(client, owner_headers, "INST-RISK-004", "SN-RISK-004")

    db_user = type("U", (), {"id": 9999, "role": type("R", (), {"value": "OWNER"})()})()
    from tests.conftest import TestSessionLocal
    from models.user import User, UserRole
    from passlib.context import CryptContext
    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    db = TestSessionLocal()
    other_owner = User(
        full_name="Other Owner", email="otherowner@test.com", phone="8888888888",
        hashed_password=pwd.hash("pass"[:72]), role=UserRole.OWNER,
    )
    db.add(other_owner)
    db.commit()
    db.refresh(other_owner)
    db.close()

    other_headers = get_auth_header(client, "otherowner@test.com", "pass")
    r = client.get(f"/api/instruments/{inst['id']}/risk", headers=other_headers)
    assert r.status_code == 403


def test_risk_nonexistent_instrument(client, owner_user):
    headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    r = client.get("/api/instruments/99999/risk", headers=headers)
    assert r.status_code == 404


def test_risk_admin_can_view(client, owner_user, admin_user):
    owner_headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    admin_headers = get_auth_header(client, "testadmin@test.com", "adminpass")

    inst = _create_instrument(client, owner_headers, "INST-RISK-005", "SN-RISK-005")
    r = client.get(f"/api/instruments/{inst['id']}/risk", headers=admin_headers)
    assert r.status_code == 200
    assert "risk_score" in r.json()
