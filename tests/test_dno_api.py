"""
FloodWatch AI — Phase 7D: Chennai Hydrodynamic DNO Test Suite
SIH26085 — High-Resolution Urban Flood Susceptibility & Safe Mobility System

Comprehensive integration and regression tests for DNO hydrodynamic inference:
1. DNO Health check (/api/v1/dno/health & /api/dno/health)
2. Available storm library events (/api/v1/dno/events)
3. Valid DNO spatiotemporal prediction (H, U, V, extent, severity)
4. Invalid event handling (HTTP 404)
5. Spatial grid extraction
6. GeoJSON export (/api/v1/dno/forecast/{event_id}/geojson)
7. Physical constraints & numerical stability (H >= 0, finite values, no NaN/Inf)
8. 10x sequential inference latency & VRAM stability test
9. CPU execution fallback
"""

import time
import pytest
import torch
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.dno_inference_service import DNOInferenceService

client = TestClient(app)


def test_dno_health_v1():
    """Verify DNO health endpoint under /api/v1/dno/health."""
    res = client.get("/api/v1/dno/health")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True
    assert data["model_name"] == "Chennai Urban Flood DNO"
    assert "phase7c-alpha1.00" in data["model_version"]
    assert data["checkpoint_sha256"] == "8c25b242b10e2bbdbee7f4a407902a045a3fe4ba55f5df4f548b1930c04126c2"
    assert data["checkpoint_size_bytes"] == 107304025
    assert data["horizon_minutes"] == 120
    assert data["timestep_minutes"] == 5
    assert "XGBoost" in data["production_separation"]
    assert "experimental hydrodynamic surrogate" in data["disclaimer"]


def test_dno_health_direct_alias():
    """Verify direct alias /api/dno/health works identically."""
    res = client.get("/api/dno/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_dno_events_list():
    """Verify listing of prepared Chennai storm events."""
    res = client.get("/api/v1/dno/events")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["total_events"] == 30
    assert len(data["events"]) == 30
    first_event = data["events"][0]
    assert first_event["id"] == "storm_001"
    assert first_event["input_tensor_exists"] is True


def test_dno_prediction_valid():
    """Verify complete spatiotemporal DNO prediction on prepared storm_011."""
    payload = {"event_id": "storm_011", "include_spatial_grids": False}
    res = client.post("/api/v1/dno/predict", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["model"] == "chennai_phase7c_dno"
    assert data["model_version"] == "phase7c-alpha1.00"
    assert data["input_mode"] == "prepared"
    assert data["event_id"] == "storm_011"
    assert data["forecast_horizon_minutes"] == 120
    assert data["timestep_minutes"] == 5
    assert data["num_timesteps"] == 24

    # Grid metadata check
    grid = data["grid"]
    assert grid["crs"] == "EPSG:32644"
    assert grid["width"] == 128
    assert grid["height"] == 128
    assert grid["cell_size_meters"] == 78.125
    assert len(grid["bounds_utm44n"]) == 4

    # Model metadata check
    meta = data["model_metadata"]
    assert meta["alpha"] == 1.0
    assert meta["threshold_m"] == 0.15
    assert meta["units"]["water_depth"] == "meters"
    assert meta["units"]["velocity_magnitude"] == "m/s"

    # Summary check
    summary = data["summary"]
    assert summary["peak_depth_m"] > 0.0
    assert summary["peak_velocity_mps"] > 0.0
    assert summary["peak_flooded_area_m2"] > 0.0

    # Timestep forecasts check
    forecasts = data["forecasts"]
    assert len(forecasts) == 24
    assert forecasts[0]["lead_minutes"] == 5
    assert forecasts[-1]["lead_minutes"] == 120

    for fc in forecasts:
        assert fc["max_depth_m"] >= 0.0
        assert fc["mean_depth_m"] >= 0.0
        assert fc["max_velocity_mps"] >= 0.0
        assert fc["flooded_area_m2"] >= 0.0

        extent = fc["flood_extent"]
        assert extent["cells_gt_0_05m"] >= extent["cells_gt_0_10m"]
        assert extent["cells_gt_0_10m"] >= extent["cells_gt_0_20m"]
        assert extent["cells_gt_0_20m"] >= extent["cells_gt_0_50m"]
        assert extent["cells_gt_0_50m"] >= extent["cells_gt_1_00m"]

        sev = fc["depth_severity_cells"]
        total_cells = sum(sev.values())
        assert total_cells == 128 * 128

    # Diagnostics check
    diag = data["diagnostics"]
    assert diag["nan_detected"] is False
    assert diag["inf_detected"] is False
    assert diag["inference_latency_ms"] > 0.0
    assert diag["total_latency_ms"] > 0.0


def test_dno_prediction_with_spatial_grid():
    """Verify optional spatial 128x128 grid inclusion for a specific lead minute."""
    payload = {
        "event_id": "storm_011",
        "include_spatial_grids": True,
        "target_lead_minutes_spatial": 60
    }
    res = client.post("/api/v1/dno/predict", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["spatial_grids"] is not None
    sg = data["spatial_grids"]
    assert sg["lead_minutes"] == 60
    assert len(sg["depth_m"]) == 128
    assert len(sg["depth_m"][0]) == 128
    assert len(sg["velocity_mps"]) == 128


def test_dno_prediction_invalid_event():
    """Verify clean 404 response for nonexistent event."""
    payload = {"event_id": "nonexistent_storm_999"}
    res = client.post("/api/v1/dno/predict", json=payload)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_dno_geojson_export():
    """Verify GeoJSON FeatureCollection generation for Adyar-Velachery pilot grid."""
    res = client.get("/api/v1/dno/forecast/storm_011/geojson?lead_minutes=60&threshold_m=0.10")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert data["properties"]["event_id"] == "storm_011"
    assert data["properties"]["lead_minutes"] == 60
    assert len(data["features"]) > 0

    first_feat = data["features"][0]
    assert first_feat["type"] == "Feature"
    assert first_feat["geometry"]["type"] == "Polygon"
    assert len(first_feat["geometry"]["coordinates"][0]) == 5  # closed polygon
    props = first_feat["properties"]
    assert props["depth_m"] >= 0.10
    assert props["velocity_mps"] >= 0.0
    assert "severity" in props


def test_dno_geojson_validation_error():
    """Verify validation error when lead_minutes is out of bounds (<5)."""
    res = client.get("/api/v1/dno/forecast/storm_011/geojson?lead_minutes=2")
    assert res.status_code == 422


def test_10x_sequential_inference_and_vram():
    """
    Test 10 sequential inferences to verify:
    1. VRAM stability (no memory leak across calls).
    2. Numerical stability (no NaNs/Infs).
    3. Low consistent inference latency.
    """
    service = DNOInferenceService.get_instance()
    test_events = ["storm_011", "storm_016", "storm_007", "storm_024", "storm_028"] * 2

    latencies = []
    initial_vram = 0
    if service.device.type == "cuda":
        torch.cuda.empty_cache()
        initial_vram = torch.cuda.memory_allocated(service.device)

    for idx, eid in enumerate(test_events, 1):
        t0 = time.perf_counter()
        res = service.predict_prepared_event(eid)
        lat = (time.perf_counter() - t0) * 1000.0
        latencies.append(lat)

        assert res["diagnostics"]["nan_detected"] is False
        assert res["diagnostics"]["inf_detected"] is False
        assert res["summary"]["peak_depth_m"] > 0.0

    if service.device.type == "cuda":
        torch.cuda.empty_cache()
        final_vram = torch.cuda.memory_allocated(service.device)
        vram_diff_mb = (final_vram - initial_vram) / (1024 * 1024)
        # VRAM must not grow continuously
        assert vram_diff_mb < 5.0, f"Possible VRAM leak: increased by {vram_diff_mb:.2f} MB"

    mean_lat = sum(latencies) / len(latencies)
    print(f"\n[PASS] 10x Sequential Inference: Mean Latency = {mean_lat:.2f} ms | Min = {min(latencies):.2f} ms | Max = {max(latencies):.2f} ms")


def test_cpu_fallback_execution():
    """Verify CPU fallback execution produces valid physical predictions."""
    cpu_service = DNOInferenceService(force_cpu=True)
    assert cpu_service.device.type == "cpu"
    res = cpu_service.predict_prepared_event("storm_011")
    assert res["model"] == "chennai_phase7c_dno"
    assert res["summary"]["peak_depth_m"] > 0.0
    assert res["diagnostics"]["nan_detected"] is False
    assert res["diagnostics"]["device"] == "cpu"
