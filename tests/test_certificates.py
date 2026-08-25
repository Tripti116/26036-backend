from tests.conftest import get_auth_header


def _create_instrument(client, headers, instrument_id, serial_number):
    r = client.post(
        "/api/instruments/",
        json={
            "instrument_id": instrument_id,
            "instrument_type": "Weighing Scale",
            "manufacturer": "Test Mfg",
            "model_number": "M-200",
            "serial_number": serial_number,
            "capacity": "50kg",
        },
        headers=headers,
    )
    return r.json()


def _full_verification_flow(client, owner_headers, admin_headers, inspector_headers, inspector_id, instrument):
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
            "expected_value": 50.0,
            "measured_value": 50.2,
            "tolerance_limit": 1.0,
            "remarks": "OK",
        },
        headers=inspector_headers,
    )
    return vid


def test_generate_certificate(client, owner_user, admin_user, inspector_user):
    owner_headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    admin_headers = get_auth_header(client, "testadmin@test.com", "adminpass")
    inspector_headers = get_auth_header(client, "testinspector@test.com", "inspectorpass")

    inst = _create_instrument(client, owner_headers, "INST-CERT-001", "SN-CERT-001")
    vid = _full_verification_flow(
        client, owner_headers, admin_headers, inspector_headers,
        inspector_user.id, inst,
    )

    r = client.post(f"/api/certificates/generate/{vid}", headers=admin_headers)
    assert r.status_code == 200
    assert "certificate_number" in r.json()


def test_duplicate_certificate_rejected(client, owner_user, admin_user, inspector_user):
    owner_headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    admin_headers = get_auth_header(client, "testadmin@test.com", "adminpass")
    inspector_headers = get_auth_header(client, "testinspector@test.com", "inspectorpass")

    inst = _create_instrument(client, owner_headers, "INST-CERTD-001", "SN-CERTD-001")
    vid = _full_verification_flow(
        client, owner_headers, admin_headers, inspector_headers,
        inspector_user.id, inst,
    )

    client.post(f"/api/certificates/generate/{vid}", headers=admin_headers)
    r = client.post(f"/api/certificates/generate/{vid}", headers=admin_headers)
    assert r.status_code == 409


def test_generate_cert_for_fail_rejected(client, owner_user, admin_user, inspector_user):
    owner_headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    admin_headers = get_auth_header(client, "testadmin@test.com", "adminpass")
    inspector_headers = get_auth_header(client, "testinspector@test.com", "inspectorpass")

    inst = _create_instrument(client, owner_headers, "INST-CERTF-001", "SN-CERTF-001")
    client.post(
        "/api/verification/request",
        json={"instrument_id": inst["id"]},
        headers=owner_headers,
    )
    r = client.get("/api/verification/", headers=admin_headers)
    pending = [v for v in r.json() if v["status"] == "PENDING"]
    vid = pending[-1]["id"]
    client.put(
        f"/api/verification/{vid}/assign",
        json={"inspector_id": inspector_user.id},
        headers=admin_headers,
    )
    client.put(
        f"/api/verification/{vid}/complete",
        json={
            "reference_standard_used": "NIST",
            "expected_value": 100.0,
            "measured_value": 110.0,
            "tolerance_limit": 1.0,
            "remarks": "Way off",
        },
        headers=inspector_headers,
    )

    r = client.post(f"/api/certificates/generate/{vid}", headers=admin_headers)
    assert r.status_code == 400


def test_list_certificates(client, owner_user, admin_user, inspector_user):
    owner_headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    admin_headers = get_auth_header(client, "testadmin@test.com", "adminpass")
    inspector_headers = get_auth_header(client, "testinspector@test.com", "inspectorpass")

    inst = _create_instrument(client, owner_headers, "INST-CERTL-001", "SN-CERTL-001")
    vid = _full_verification_flow(
        client, owner_headers, admin_headers, inspector_headers,
        inspector_user.id, inst,
    )
    client.post(f"/api/certificates/generate/{vid}", headers=admin_headers)

    r = client.get("/api/certificates/", headers=admin_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_public_verify(client, owner_user, admin_user, inspector_user):
    owner_headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    admin_headers = get_auth_header(client, "testadmin@test.com", "adminpass")
    inspector_headers = get_auth_header(client, "testinspector@test.com", "inspectorpass")

    inst = _create_instrument(client, owner_headers, "INST-PUB-001", "SN-PUB-001")
    vid = _full_verification_flow(
        client, owner_headers, admin_headers, inspector_headers,
        inspector_user.id, inst,
    )
    cert_resp = client.post(f"/api/certificates/generate/{vid}", headers=admin_headers)
    cert_number = cert_resp.json()["certificate_number"]

    r = client.get(f"/api/public/verify/{cert_number}")
    assert r.status_code == 200
    data = r.json()
    assert data["certificate_number"] == cert_number
    assert data["status"] == "VALID"


def test_public_verify_nonexistent(client):
    r = client.get("/api/public/verify/CERT-9999-999999")
    assert r.status_code == 404


def test_expired_certificate_detected(client, owner_user, admin_user, inspector_user):
    from datetime import datetime, timedelta, timezone
    from models.certificate import Certificate, CertificateStatus
    from tests.conftest import TestSessionLocal

    owner_headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    admin_headers = get_auth_header(client, "testadmin@test.com", "adminpass")
    inspector_headers = get_auth_header(client, "testinspector@test.com", "inspectorpass")

    inst = _create_instrument(client, owner_headers, "INST-EXP-001", "SN-EXP-001")
    vid = _full_verification_flow(
        client, owner_headers, admin_headers, inspector_headers,
        inspector_user.id, inst,
    )
    cert_resp = client.post(f"/api/certificates/generate/{vid}", headers=admin_headers)
    cert_number = cert_resp.json()["certificate_number"]

    db = TestSessionLocal()
    cert = db.query(Certificate).filter(Certificate.certificate_number == cert_number).first()
    cert.valid_until = datetime.now(timezone.utc) - timedelta(days=30)
    db.commit()
    db.close()

    r = client.get(f"/api/public/verify/{cert_number}")
    assert r.status_code == 200
    assert r.json()["status"] == "EXPIRED"


def test_unauthorized_certificate_access(client, owner_user):
    headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    r = client.get("/api/certificates/99999", headers=headers)
    assert r.status_code == 404


def test_unauthenticated_public_verify(client):
    r = client.get("/api/public/verify/CERT-0000-000001")
    assert r.status_code == 404
