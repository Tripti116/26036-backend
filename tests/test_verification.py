from tests.conftest import get_auth_header


def _create_instrument(client, owner_headers, instrument_id, serial_number):
    r = client.post(
        "/api/instruments/",
        json={
            "instrument_id": instrument_id,
            "instrument_type": "Weighing Scale",
            "manufacturer": "Test Mfg",
            "model_number": "M-100",
            "serial_number": serial_number,
            "capacity": "100kg",
        },
        headers=owner_headers,
    )
    return r.json()


def test_request_verification(client, owner_user):
    headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    inst = _create_instrument(client, headers, "INST-VR-001", "SN-VR-001")
    r = client.post(
        "/api/verification/request",
        json={"instrument_id": inst["id"]},
        headers=headers,
    )
    assert r.status_code == 200
    assert "verification_id" in r.json()


def test_request_verification_not_owner(client, admin_user):
    headers = get_auth_header(client, "testadmin@test.com", "adminpass")
    r = client.post(
        "/api/verification/request",
        json={"instrument_id": 9999},
        headers=headers,
    )
    assert r.status_code == 403


def test_assign_inspector(client, owner_user, admin_user, inspector_user):
    owner_headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    inst = _create_instrument(client, owner_headers, "INST-AS-001", "SN-AS-001")
    client.post(
        "/api/verification/request",
        json={"instrument_id": inst["id"]},
        headers=owner_headers,
    )

    admin_headers = get_auth_header(client, "testadmin@test.com", "adminpass")
    r = client.get("/api/verification/", headers=admin_headers)
    verifications = r.json()
    pending = [v for v in verifications if v["status"] == "PENDING"]
    vid = pending[-1]["id"]

    r = client.put(
        f"/api/verification/{vid}/assign",
        json={"inspector_id": inspector_user.id},
        headers=admin_headers,
    )
    assert r.status_code == 200


def test_complete_verification_pass(client, owner_user, admin_user, inspector_user):
    owner_headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    inst = _create_instrument(client, owner_headers, "INST-CV-001", "SN-CV-001")
    client.post(
        "/api/verification/request",
        json={"instrument_id": inst["id"]},
        headers=owner_headers,
    )

    admin_headers = get_auth_header(client, "testadmin@test.com", "adminpass")
    r = client.get("/api/verification/", headers=admin_headers)
    verifications = r.json()
    pending = [v for v in verifications if v["status"] == "PENDING"]
    vid = pending[-1]["id"]

    inspector_headers = get_auth_header(client, "testinspector@test.com", "inspectorpass")
    client.put(
        f"/api/verification/{vid}/assign",
        json={"inspector_id": inspector_user.id},
        headers=admin_headers,
    )

    r = client.put(
        f"/api/verification/{vid}/complete",
        json={
            "reference_standard_used": "NIST Standard",
            "expected_value": 100.0,
            "measured_value": 100.5,
            "tolerance_limit": 1.0,
            "remarks": "Within tolerance",
        },
        headers=inspector_headers,
    )
    assert r.status_code == 200
    assert r.json()["result"] == "PASS"


def test_complete_verification_fail(client, owner_user, admin_user, inspector_user):
    owner_headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    inst = _create_instrument(client, owner_headers, "INST-CVF-001", "SN-CVF-001")
    client.post(
        "/api/verification/request",
        json={"instrument_id": inst["id"]},
        headers=owner_headers,
    )

    admin_headers = get_auth_header(client, "testadmin@test.com", "adminpass")
    r = client.get("/api/verification/", headers=admin_headers)
    verifications = r.json()
    pending = [v for v in verifications if v["status"] == "PENDING"]
    vid = pending[-1]["id"]

    inspector_headers = get_auth_header(client, "testinspector@test.com", "inspectorpass")
    client.put(
        f"/api/verification/{vid}/assign",
        json={"inspector_id": inspector_user.id},
        headers=admin_headers,
    )

    r = client.put(
        f"/api/verification/{vid}/complete",
        json={
            "reference_standard_used": "NIST Standard",
            "expected_value": 100.0,
            "measured_value": 105.0,
            "tolerance_limit": 1.0,
            "remarks": "Exceeds tolerance",
        },
        headers=inspector_headers,
    )
    assert r.status_code == 200
    assert r.json()["result"] == "FAIL"


def test_deviation_calculation(client, owner_user, admin_user, inspector_user):
    owner_headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    inst = _create_instrument(client, owner_headers, "INST-DEV-001", "SN-DEV-001")
    client.post(
        "/api/verification/request",
        json={"instrument_id": inst["id"]},
        headers=owner_headers,
    )

    admin_headers = get_auth_header(client, "testadmin@test.com", "adminpass")
    r = client.get("/api/verification/", headers=admin_headers)
    verifications = r.json()
    pending = [v for v in verifications if v["status"] == "PENDING"]
    vid = pending[-1]["id"]

    inspector_headers = get_auth_header(client, "testinspector@test.com", "inspectorpass")
    client.put(
        f"/api/verification/{vid}/assign",
        json={"inspector_id": inspector_user.id},
        headers=admin_headers,
    )

    r = client.put(
        f"/api/verification/{vid}/complete",
        json={
            "reference_standard_used": "ISO Standard",
            "expected_value": 200.0,
            "measured_value": 206.0,
            "tolerance_limit": 2.0,
            "remarks": "Testing deviation",
        },
        headers=inspector_headers,
    )
    assert r.status_code == 200
    data = r.json()
    expected_deviation = abs(206.0 - 200.0) / 200.0 * 100
    assert abs(data["deviation_percentage"] - expected_deviation) < 0.001
    assert data["result"] == "FAIL"


def test_expected_value_zero_rejected(client, owner_user, admin_user, inspector_user):
    owner_headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    inst = _create_instrument(client, owner_headers, "INST-ZERO-001", "SN-ZERO-001")
    client.post(
        "/api/verification/request",
        json={"instrument_id": inst["id"]},
        headers=owner_headers,
    )

    admin_headers = get_auth_header(client, "testadmin@test.com", "adminpass")
    r = client.get("/api/verification/", headers=admin_headers)
    verifications = r.json()
    pending = [v for v in verifications if v["status"] == "PENDING"]
    vid = pending[-1]["id"]

    inspector_headers = get_auth_header(client, "testinspector@test.com", "inspectorpass")
    client.put(
        f"/api/verification/{vid}/assign",
        json={"inspector_id": inspector_user.id},
        headers=admin_headers,
    )

    r = client.put(
        f"/api/verification/{vid}/complete",
        json={
            "reference_standard_used": "Standard",
            "expected_value": 0.0,
            "measured_value": 0.0,
            "tolerance_limit": 1.0,
        },
        headers=inspector_headers,
    )
    assert r.status_code == 400


def test_duplicate_pending_verification_rejected(client, owner_user):
    headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    inst = _create_instrument(client, headers, "INST-DUPV-001", "SN-DUPV-001")
    client.post(
        "/api/verification/request",
        json={"instrument_id": inst["id"]},
        headers=headers,
    )
    r = client.post(
        "/api/verification/request",
        json={"instrument_id": inst["id"]},
        headers=headers,
    )
    assert r.status_code == 409
