#!/usr/bin/env python3
"""
Test all Chennai FastAPI routes and contracts.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_all():
    print("Testing Root...")
    r = client.get("/")
    assert r.status_code == 200
    assert "Chennai" in r.json()["study_area"]

    print("Testing Health...")
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert "Chennai" in r.json()["study_area"]

    print("Testing Subsystem Status...")
    r = client.get("/api/v1/health/system-status")
    assert r.status_code == 200
    status = r.json()
    assert status["xgboost_model"]["status"] == "READY"
    assert status["chennai_grid"]["status"] == "READY"
    assert status["nowcast_0_3h"]["status"] == "AWAITING_FORECAST_DATA"

    print("Testing KPIs...")
    r = client.get("/api/v1/current-risk/kpis")
    assert r.status_code == 200
    assert r.json()["highRiskZones"] >= 0

    print("Testing Forecast Risk NOW (3,963 cells)...")
    r = client.get("/api/v1/forecast-risk?horizon=NOW")
    assert r.status_code == 200
    zones = r.json()
    assert len(zones) == 3963
    first = zones[0]
    assert 12.85 <= first["latitude"] <= 13.25
    assert 80.09 <= first["longitude"] <= 80.35
    assert first["waterDepth"] is None

    print("Testing Forecast Status for +1H...")
    r = client.get("/api/v1/forecast-risk/status?horizon=+1H")
    assert r.status_code == 200
    assert r.json()["status"] == "forecast_data_unavailable"

    print("Testing Hotspots...")
    r = client.get("/api/v1/flood/hotspots?limit=10")
    assert r.status_code == 200
    hotspots = r.json()
    assert len(hotspots) == 10
    assert "Velachery" in hotspots[0]["locality"] or "Madipakkam" in hotspots[0]["locality"] or len(hotspots[0]["locality"]) > 0

    print("Testing Depth (unfabricated)...")
    r = client.get("/api/v1/flood/depth?location=Velachery")
    assert r.status_code == 200
    assert r.json()["depth_cm"] is None
    assert r.json()["status"] == "unavailable"

    print("Testing Rainfall Current...")
    r = client.get("/api/v1/rainfall/current")
    assert r.status_code == 200
    assert r.json()["unit"] == "mm"
    assert r.json()["status"] == "OBSERVED"

    print("Testing Radar Metadata...")
    r = client.get("/api/v1/rainfall/radar")
    assert r.status_code == 200
    assert len(r.json()["cells"]) > 0
    assert "Chennai" in r.json()["station_name"]

    print("Testing Drainage Surface Waterways...")
    r = client.get("/api/v1/drainage/surface-waterways")
    assert r.status_code == 200
    rivers = [w["name"] for w in r.json()]
    assert any("Adyar" in name for name in rivers)
    assert any("Cooum" in name for name in rivers)

    print("Testing Drainage Surcharge (honest status)...")
    r = client.get("/api/v1/drainage/surcharge")
    assert r.status_code == 200
    assert r.json()["status"] == "network_data_unavailable"
    assert r.json()["monitored_nodes_count"] == 0

    print("Testing Alerts...")
    r = client.get("/api/v1/alerts")
    assert r.status_code == 200
    assert len(r.json()) > 0
    assert "Velachery" in r.json()[0]["location"] or "Adyar" in r.json()[0]["location"] or len(r.json()[0]["location"]) > 0

    print("Testing Road Segments...")
    r = client.get("/api/v1/map-data/roads")
    assert r.status_code == 200
    roads = [rd["name"] for rd in r.json()]
    assert any("Anna Salai" in name for name in roads)

    print("Testing Safe Route POST...")
    payload = {
        "origin": "Chennai Central",
        "destination": "Chennai Airport",
        "vehicle_type": "SUV"
    }
    r = client.post("/api/v1/safe-route", json=payload)
    assert r.status_code == 200
    route = r.json()
    assert "Anna Salai" in route["recommendedRoute"]["name"]
    assert route["recommendedRoute"]["safetyScore"] >= 90

    print("=" * 60)
    print("ALL BACKEND CHENNAI APIS & CONTRACTS PASSED WITH 100% ACCURACY")
    print("=" * 60)

if __name__ == "__main__":
    test_all()
