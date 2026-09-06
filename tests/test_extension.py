import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.session import SessionLocal
from backend.app.db.init_db import init_db

# Initialize DB for tests
db = SessionLocal()
init_db(db)
db.close()

client = TestClient(app)

import time

def test_citizen_registration():
    ts = int(time.time() * 1000)
    unique_email = f"test.citizen.{ts}@mumbai.in"
    unique_mobile = f"+9198{str(ts)[-8:]}"
    res = client.post("/api/v1/auth/register", json={
        "full_name": "Test Citizen",
        "email": unique_email,
        "mobile": unique_mobile,
        "password": "Password@123",
        "confirm_password": "Password@123",
        "preferred_language": "en",
        "alert_preferences": {
            "flood_alerts_enabled": True,
            "location_alerts_enabled": True
        }
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "CITIZEN"

    # Duplicate rejection
    dup_res = client.post("/api/v1/auth/register", json={
        "full_name": "Duplicate Test",
        "email": unique_email,
        "mobile": "+919899999992",
        "password": "Password@123",
        "confirm_password": "Password@123"
    })
    assert dup_res.status_code == 400

def test_login_and_roles():
    # 1. Admin login
    res_admin = client.post("/api/v1/auth/login", json={
        "login_id": "admin@floodwatch.mumbai.gov.in",
        "password": "Admin@Mumbai2026"
    })
    assert res_admin.status_code == 200
    assert res_admin.json()["user"]["role"] == "ADMIN"

    # 2. Verified Gov login
    res_gov = client.post("/api/v1/auth/login", json={
        "login_id": "eoc.officer@mcgm.gov.in",
        "password": "Gov@Mumbai2026"
    })
    assert res_gov.status_code == 200
    assert res_gov.json()["user"]["role"] == "GOVERNMENT_OPERATOR"

    # 3. Invalid login
    res_invalid = client.post("/api/v1/auth/login", json={
        "login_id": "admin@floodwatch.mumbai.gov.in",
        "password": "WrongPassword!"
    })
    assert res_invalid.status_code == 401

def test_otp_flow():
    # Send OTP
    send_res = client.post("/api/v1/auth/send-email-otp", json={
        "target": "verify.test@mumbai.in",
        "purpose": "REGISTRATION"
    })
    assert send_res.status_code == 200
    assert send_res.json()["is_mock"] is True

    # Test invalid OTP
    bad_verify = client.post("/api/v1/auth/verify-email-otp", json={
        "target": "verify.test@mumbai.in",
        "otp_code": "000000",
        "purpose": "REGISTRATION"
    })
    assert bad_verify.status_code == 400

def test_rbac_restrictions():
    # Citizen token
    res_cit = client.post("/api/v1/auth/login", json={
        "login_id": "rohan.citizen@gmail.com",
        "password": "Citizen@2026"
    })
    cit_token = res_cit.json()["access_token"]
    cit_headers = {"Authorization": f"Bearer {cit_token}"}

    # Citizen accessing Admin API -> 403
    res_admin_api = client.get("/api/v1/admin/users", headers=cit_headers)
    assert res_admin_api.status_code == 403

    # Citizen accessing Government Dashboard -> 403
    res_gov_api = client.get("/api/v1/government/dashboard", headers=cit_headers)
    assert res_gov_api.status_code == 403

    # Pending Government accessing Government Dashboard -> 403
    res_pending = client.post("/api/v1/auth/login", json={
        "login_id": "ward.trainee@mcgm.gov.in",
        "password": "Pending@2026"
    })
    pending_token = res_pending.json()["access_token"]
    pending_headers = {"Authorization": f"Bearer {pending_token}"}
    res_pending_dash = client.get("/api/v1/government/dashboard", headers=pending_headers)
    assert res_pending_dash.status_code == 403

    # Verified Government accessing Government Dashboard -> 200
    res_gov_verified = client.post("/api/v1/auth/login", json={
        "login_id": "eoc.officer@mcgm.gov.in",
        "password": "Gov@Mumbai2026"
    })
    gov_token = res_gov_verified.json()["access_token"]
    gov_headers = {"Authorization": f"Bearer {gov_token}"}
    res_gov_dash = client.get("/api/v1/government/dashboard", headers=gov_headers)
    assert res_gov_dash.status_code == 200
    data = res_gov_dash.json()
    assert "eligible_opted_in_citizens" in data
    assert "successfully_notified" in data

def test_location_and_privacy():
    res_cit = client.post("/api/v1/auth/login", json={
        "login_id": "rohan.citizen@gmail.com",
        "password": "Citizen@2026"
    })
    cit_headers = {"Authorization": f"Bearer {res_cit.json()['access_token']}"}

    # 1. Update without consent -> 400
    no_consent = client.post("/api/v1/location/update", headers=cit_headers, json={
        "latitude": 19.0125,
        "longitude": 72.8428,
        "accuracy_meters": 10.0,
        "consent_status": False
    })
    assert no_consent.status_code == 400

    # 2. Update with consent -> 200
    with_consent = client.post("/api/v1/location/update", headers=cit_headers, json={
        "latitude": 19.0125,
        "longitude": 72.8428,
        "accuracy_meters": 12.0,
        "consent_status": True
    })
    assert with_consent.status_code == 200
    assert with_consent.json()["consent_status"] is True

    # 3. Get current location
    cur = client.get("/api/v1/location/current", headers=cit_headers)
    assert cur.status_code == 200
    assert cur.json()["latitude"] == 19.0125

    # 4. Delete current session location
    del_cur = client.delete("/api/v1/location/current", headers=cit_headers)
    assert del_cur.status_code == 200
    cur_after = client.get("/api/v1/location/current", headers=cit_headers)
    assert cur_after.status_code == 404

def test_targeted_alerts():
    # Update location back to Hindmata (near 19.0125, 72.8428)
    res_cit = client.post("/api/v1/auth/login", json={
        "login_id": "rohan.citizen@gmail.com",
        "password": "Citizen@2026"
    })
    cit_headers = {"Authorization": f"Bearer {res_cit.json()['access_token']}"}
    client.post("/api/v1/location/update", headers=cit_headers, json={
        "latitude": 19.0125,
        "longitude": 72.8428,
        "accuracy_meters": 8.0,
        "consent_status": True
    })

    # Fetch targeted alerts
    alerts_res = client.get("/api/v1/alerts/my-alerts", headers=cit_headers)
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) > 0
    first_deliv = alerts[0]
    assert "Hindmata" in first_deliv["title"] or "Milan" in first_deliv["title"]

    # Mark as read
    deliv_id = first_deliv["delivery_id"]
    read_res = client.patch(f"/api/v1/alerts/{deliv_id}/read", headers=cit_headers)
    assert read_res.status_code == 200

def test_citizen_feedback_and_evaluation():
    res_cit = client.post("/api/v1/auth/login", json={
        "login_id": "rohan.citizen@gmail.com",
        "password": "Citizen@2026"
    })
    cit_headers = {"Authorization": f"Bearer {res_cit.json()['access_token']}"}

    # Submit flood report
    rep_res = client.post("/api/v1/feedback/flood-report", headers=cit_headers, json={
        "latitude": 19.0125,
        "longitude": 72.8428,
        "location_name": "Hindmata Junction",
        "observation_status": "YES",
        "water_level": "HIGH",
        "description": "Water reached knee level on Dr. Ambedkar Road.",
        "linked_grid_id": "MUM_G101"
    })
    assert rep_res.status_code == 200
    rep_id = rep_res.json()["id"]
    assert rep_res.json()["validation_status"] == "UNVERIFIED"

    # Admin reviews report
    res_admin = client.post("/api/v1/auth/login", json={
        "login_id": "admin@floodwatch.mumbai.gov.in",
        "password": "Admin@Mumbai2026"
    })
    admin_headers = {"Authorization": f"Bearer {res_admin.json()['access_token']}"}

    review_res = client.patch(f"/api/v1/admin/feedback/{rep_id}/review", headers=admin_headers, json={
        "validation_status": "VALIDATED",
        "admin_notes": "Confirmed by Ward F/South on-ground spotter."
    })
    assert review_res.status_code == 200
    assert review_res.json()["validation_status"] == "VALIDATED"

    # Fetch ground truth evaluation
    eval_res = client.get("/api/v1/admin/model-evaluation", headers=admin_headers)
    assert eval_res.status_code == 200
    data = eval_res.json()
    assert "accuracy_alignment_pct" in data
    assert data["potential_true_positives"] >= 1
