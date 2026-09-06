import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "FloodWatch AI"
    assert "Mumbai" in data["study_area"]

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_kpis():
    response = client.get("/api/v1/current-risk/kpis")
    assert response.status_code == 200
    data = response.json()
    assert "currentRainfall" in data
    assert "highRiskZones" in data
    assert data["isSimulated"] is False

def test_forecast_risk():
    response = client.get("/api/v1/forecast-risk?horizon=NOW")
    assert response.status_code == 200
    zones = response.json()
    assert len(zones) > 1000
    assert zones[0]["isSimulated"] is False
    assert "riskScore" in zones[0]

def test_safe_route():
    response = client.post("/api/v1/safe-route", json={"source": "Dadar", "destination": "Andheri"})
    assert response.status_code == 200
    data = response.json()
    assert data["recommendedRoute"]["safetyScore"] > data["alternativeRoute"]["safetyScore"]
    assert len(data["recommendedRoute"]["pathCoordinates"]) > 2
    assert len(data["hazards"]) >= 2

def test_alerts():
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    alerts = response.json()
    assert len(alerts) >= 4
    # Test acknowledge
    alt_id = alerts[0]["id"]
    ack_res = client.patch(f"/api/v1/alerts/{alt_id}/acknowledge")
    assert ack_res.status_code == 200
    assert ack_res.json()["acknowledged"] is True

def test_analytics():
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert len(data["areaRankings"]) > 0
    assert len(data["rainfallTrends"]) > 0

def test_system_overview():
    response = client.get("/api/v1/health/system-overview")
    assert response.status_code == 200
    data = response.json()
    assert data["modelMetrics"]["algorithm"] == "Gradient Boosted Decision Trees (XGBoostClassifier)"
    assert data["modelMetrics"]["prototypeF1Score"] > 0.90
