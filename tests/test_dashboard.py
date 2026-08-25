from tests.conftest import get_auth_header


def test_dashboard_summary(client, admin_user):
    headers = get_auth_header(client, "testadmin@test.com", "adminpass")
    r = client.get("/api/dashboard/summary", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "total_users" in data
    assert "total_instruments" in data
    assert "pending_verifications" in data
    assert "completed_verifications" in data
    assert "passed_instruments" in data
    assert "failed_instruments" in data
    assert "valid_certificates" in data
    assert "expired_certificates" in data


def test_dashboard_non_admin_forbidden(client, owner_user):
    headers = get_auth_header(client, "testowner@test.com", "ownerpass")
    r = client.get("/api/dashboard/summary", headers=headers)
    assert r.status_code == 403


def test_dashboard_inspector_forbidden(client, inspector_user):
    headers = get_auth_header(client, "testinspector@test.com", "inspectorpass")
    r = client.get("/api/dashboard/summary", headers=headers)
    assert r.status_code == 403
