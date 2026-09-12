# CHENNAI DNO PHASE 7D — FASTAPI INTEGRATION & INFERENCE SPECIFICATION

## 1. Objective
Phase 7D integrates the selected Chennai Phase 7C Deep Neural Operator (DNO) model (`best_alpha_1.00_checkpoint.pt`) into the existing FloodWatch AI FastAPI backend as an **isolated experimental hydrodynamic inference service**.
The service provides spatiotemporal forecasts of water depth ($H$), velocity vector components ($U, V$), velocity magnitude ($W = \sqrt{U^2 + V^2}$), and derived flood products (inundated extent, thresholded areas, depth severity classification, and GeoJSON contours) over a 120-minute horizon ($24 \times 5$-minute intervals) on the 10 km $\times$ 10 km Adyar–Velachery pilot domain.

---

## 2. Selected Model
- **Model Architecture**: Deep Neural Operator (DNO) with 3D Fourier integral operator blocks
- **Training Configuration**: Chennai Phase 7C Dual-Regime Depth Loss Experiment
- **Hyperparameters**:
  - `num_channels`: 5
  - `width`: 10
  - `initial_step`: 1
  - `pad`: 0
  - `factor`: 1
- **Loss Formulation**: Thresholded Dual-Regime Loss
  $$\begin{aligned}
  w(H) &= 1.0 \quad \text{if } H \le 0.15\text{ m} \\
  w(H) &= 1.0 + \alpha \sqrt{H - 0.15} \quad \text{if } H > 0.15\text{ m}
  \end{aligned}$$
  with $\alpha = 1.00$, threshold $= 0.15\text{ m}$.
- **Alternative Experimental Candidate**: $\alpha = 1.25$ (`best_alpha_1.25_checkpoint.pt`).

---

## 3. Model Checkpoint
- **Primary Checkpoint**: `models/urban_flood_dno/checkpoints/chennai_phase7c/best_alpha_1.00_checkpoint.pt`
- **File Size**: `107,304,025 bytes` (102.3 MB)
- **Best Training Epoch**: Epoch 47
- **Selection Basis**: Phase 7C validation audit across 4 independent validation storms, yielding the best compromise between thin-film runoff preservation and deep pooling inundation.

---

## 4. Model Hash & Integrity
- **Algorithm**: SHA-256
- **Primary Model Checkpoint Hash**:
  ```text
  8c25b242b10e2bbdbee7f4a407902a045a3fe4ba55f5df4f548b1930c04126c2
  ```
- **Experimental Alternative ($\alpha=1.25$) Checkpoint Hash**:
  ```text
  3612b655f79976f77a3be20d782042d8d7ea3c09da879b30719ee967d07dbdc4
  ```
The service verifies this hash and file size upon startup to prevent accidental corruption or altered weights.

---

## 5. Input Contract
The DNO operates strictly on standardized spatiotemporal hydrodynamic tensors conforming to the UrbanFloodCast DNO tensor schema:
- **Conceptual Structure**: `[B, Sy, Sx, T, Tin, C]`
- **Concrete Dimensions**: `[1, 128, 128, 24, 1, 5]`
  - `B = 1`: Single storm batch
  - `Sy = 128`: Grid height (North–South axis)
  - `Sx = 128`: Grid width (East–West axis)
  - `T = 24`: Forecast lead timesteps ($24 \times 5\text{ min} = 120\text{ min}$)
  - `Tin = 1`: Input history lead step
  - `C = 5`: 5 Input physical channels:
    1. $H_0$: Initial water depth (m)
    2. $U_0$: Initial velocity $x$-component (m/s)
    3. $V_0$: Initial velocity $y$-component (m/s)
    4. $P$: Precipitation forcing rate field (mm/hr)
    5. $Z$: Digital Elevation Model topography elevation (m MSL)
- **Operational Mode**: The API explicitly returns `input_mode="prepared"`. Inputs are drawn from the validated Chennai storm library.

---

## 6. Preprocessing Contract
Input tensors are normalized using the calibrated Chennai pilot statistics:
$$\begin{aligned}
\mu_H &= 0.05\text{ m}, \quad \sigma_H = 0.20\text{ m} \\
\mu_U &= 0.00\text{ m/s}, \quad \sigma_U = 0.15\text{ m/s} \\
\mu_V &= 0.00\text{ m/s}, \quad \sigma_V = 0.15\text{ m/s} \\
\mu_P &= 30.0\text{ mm/hr}, \quad \sigma_P = 25.0\text{ mm/hr} \\
\mu_Z &= 11.2\text{ m MSL}, \quad \sigma_Z = 8.5\text{ m MSL}
\end{aligned}$$

---

## 7. Output Contract
- **Model Output Tensor**: `[1, 128, 128, 24, 3]`
  - Channel 0: Water depth $H$ (meters)
  - Channel 1: Velocity $x$-component $U$ (m/s)
  - Channel 2: Velocity $y$-component $V$ (m/s)
- **Physical Non-Negativity**: In accordance with hydrodynamic principles, dry-bed numerical oscillations are filtered via $H = \max(0, H_{\text{pred}})$.
- **Target Scaling Rule**: Native physical scale. **No $\times 5$ target multiplier or arbitrary scaling factors are applied.**
- **Derived Products**:
  - Velocity magnitude: $W = \sqrt{U^2 + V^2}$ (m/s)
  - Flood extent at thresholds: $>0.05\text{ m}$, $>0.10\text{ m}$, $>0.20\text{ m}$, $>0.50\text{ m}$, $>1.00\text{ m}$ (inundated cell count and flooded area in $\text{m}^2$)
  - Depth severity classification bins:
    - Dry / Minimal wetting: $< 0.05\text{ m}$
    - Low: $0.05 - 0.10\text{ m}$
    - Minor: $0.10 - 0.20\text{ m}$
    - Moderate: $0.20 - 0.50\text{ m}$
    - Severe: $0.50 - 1.00\text{ m}$
    - Very Severe: $1.00 - 2.00\text{ m}$
    - Extreme Deep Pooling: $> 2.00\text{ m}$

---

## 8. API Endpoints
All DNO endpoints are isolated behind experimental routes:
- `GET  /api/v1/dno/health` (and direct alias `GET /api/dno/health`)
- `POST /api/v1/dno/predict` (and direct alias `POST /api/dno/predict`)
- `GET  /api/v1/dno/events` (and direct alias `GET /api/dno/events`)
- `GET  /api/v1/dno/forecast/{event_id}/geojson` (and direct alias `GET /api/dno/forecast/{event_id}/geojson`)

---

## 9. Forecast Horizon
- **Total Forecast Window**: 120 minutes (2.0 hours)
- **Timestep Resolution**: 5 minutes
- **Exposed Lead Steps**:
  $$T+5, T+10, T+15, \dots, T+120\text{ min (24 total steps)}$$
- *Note: The system explicitly exposes 120 minutes and does not claim $T+180$.*

---

## 10. Grid Metadata
- **Domain**: Adyar–Velachery Basin, Greater Chennai Corporation (GCC)
- **Coordinate Reference System (CRS)**: `EPSG:32644` (WGS 84 / UTM Zone 44N)
- **Grid Dimensions**: 128 rows $\times$ 128 columns ($16,384$ total cells)
- **Cell Size ($\Delta x, \Delta y$)**: 78.125 meters
- **Cell Footprint Area**: $6,103.515625\text{ m}^2$ (~$0.0061\text{ km}^2$)
- **Domain Physical Size**: 10.0 km $\times$ 10.0 km ($100.0\text{ km}^2$)
- **UTM Zone 44N Bounding Box**:
  - $X_{\min} = 410000.0\text{ m}$
  - $Y_{\min} = 1431000.0\text{ m}$
  - $X_{\max} = 420000.0\text{ m}$
  - $Y_{\max} = 1441000.0\text{ m}$
- **WGS 84 Geographic Bounds**:
  - $\text{Lat}_{\min} = 12.943196^\circ\text{N}, \quad \text{Lat}_{\max} = 13.033893^\circ\text{N}$
  - $\text{Lon}_{\min} = 80.170273^\circ\text{E}, \quad \text{Lon}_{\max} = 80.262192^\circ\text{E}$

---

## 11. Units
- Water Depth ($H$): `meters (m)`
- Velocity Components ($U, V$): `meters per second (m/s)`
- Velocity Magnitude ($W$): `meters per second (m/s)`
- Flooded Area: `square meters (m²)` and `square kilometers (km²)`
- Spatial Resolution: `meters (m)`
- Precipitation: `millimeters per hour (mm/hr)`

---

## 12. Example Requests

### Health Check
```bash
curl -X GET "http://localhost:8000/api/v1/dno/health"
```

### Run Hydrodynamic Prediction
```bash
curl -X POST "http://localhost:8000/api/v1/dno/predict" \
     -H "Content-Type: application/json" \
     -d '{"event_id": "storm_011", "include_spatial_grids": false}'
```

### Export GeoJSON Inundation Polygons
```bash
curl -X GET "http://localhost:8000/api/v1/dno/forecast/storm_011/geojson?lead_minutes=60&threshold_m=0.10"
```

---

## 13. Example Responses

### `GET /api/v1/dno/health`
```json
{
  "status": "ok",
  "model_loaded": true,
  "model_name": "Chennai Urban Flood DNO",
  "model_version": "phase7c-alpha1.00",
  "checkpoint_sha256": "8c25b242b10e2bbdbee7f4a407902a045a3fe4ba55f5df4f548b1930c04126c2",
  "checkpoint_size_bytes": 107304025,
  "device": "cuda:0",
  "horizon_minutes": 120,
  "timestep_minutes": 5,
  "memory_diagnostics": {
    "device": "cuda:0",
    "cuda_vram_allocated_mb": 42.8,
    "model_load_ms": 1388.99
  },
  "production_separation": "Production: XGBoost flood-risk model (Primary operational classifier, unchanged). Experimental: Phase 7C DNO hydrodynamic depth/velocity model (Isolated surrogate service).",
  "disclaimer": "This DNO model is an experimental hydrodynamic surrogate trained and evaluated on the current Chennai research dataset. It is not yet an operational government flood-warning system. The current DNO horizon is 120 minutes. Live operational rainfall/NWP coupling is not claimed unless actually implemented and verified."
}
```

### `POST /api/v1/dno/predict`
```json
{
  "model": "chennai_phase7c_dno",
  "model_version": "phase7c-alpha1.00",
  "input_mode": "prepared",
  "event_id": "storm_011",
  "forecast_horizon_minutes": 120,
  "timestep_minutes": 5,
  "num_timesteps": 24,
  "grid": {
    "crs": "EPSG:32644",
    "domain_name": "Adyar–Velachery Basin (Greater Chennai)",
    "width": 128,
    "height": 128,
    "cell_size_meters": 78.125,
    "cell_area_m2": 6103.515625,
    "bounds_utm44n": [410000.0, 1431000.0, 420000.0, 1441000.0],
    "bounds_wgs84": {
      "min_lat": 12.943196,
      "max_lat": 13.033893,
      "min_lon": 80.170273,
      "max_lon": 80.262192
    }
  },
  "summary": {
    "peak_depth_m": 0.8201,
    "peak_velocity_mps": 0.1801,
    "peak_flooded_area_m2": 4547119.1,
    "peak_flooded_area_km2": 4.547,
    "total_domain_area_km2": 100.0
  },
  "forecasts": [
    {
      "lead_minutes": 5,
      "timestep_index": 1,
      "max_depth_m": 0.1245,
      "mean_depth_m": 0.0031,
      "flooded_area_m2": 244140.6,
      "max_velocity_mps": 0.0412,
      "mean_velocity_mps": 0.0012,
      "flood_extent": {
        "cells_gt_0_05m": 40,
        "area_m2_gt_0_05m": 244140.6,
        "cells_gt_0_10m": 4,
        "area_m2_gt_0_10m": 24414.1,
        "cells_gt_0_20m": 0,
        "area_m2_gt_0_20m": 0.0,
        "cells_gt_0_50m": 0,
        "area_m2_gt_0_50m": 0.0,
        "cells_gt_1_00m": 0,
        "area_m2_gt_1_00m": 0.0
      },
      "depth_severity_cells": {
        "dry_under_5cm": 16344,
        "low_5_to_10cm": 36,
        "minor_10_to_20cm": 4,
        "moderate_20_to_50cm": 0,
        "severe_50cm_to_1m": 0,
        "very_severe_1_to_2m": 0,
        "extreme_over_2m": 0
      }
    }
  ],
  "diagnostics": {
    "device": "cuda:0",
    "inference_latency_ms": 21.49,
    "postprocessing_latency_ms": 46.83,
    "total_latency_ms": 106.70,
    "nan_detected": false,
    "inf_detected": false,
    "model_load_latency_ms": 1388.99
  },
  "disclaimer": "This DNO model is an experimental hydrodynamic surrogate..."
}
```

---

## 14. Error Handling
- **Nonexistent Event (HTTP 404)**: Clean JSON payload explaining that the prepared tensor was not found.
- **Invalid Parameter Range (HTTP 422)**: FastAPI / Pydantic validation on `lead_minutes` ($5 \le \text{min} \le 120$) and `threshold_m` ($0.01 \le \text{m} \le 5.0$).
- **Invalid Tensor Dimensions (HTTP 400)**: Rejects malformed tensors.
- **Inference Failure (HTTP 500)**: Clean error message without leaking internal Python stack traces.

---

## 15. Performance
Benchmarked on NVIDIA GPU hardware (CUDA 12.6, PyTorch 2.14.0):
- **Model Load Time**: $1,388.99\text{ ms}$ (one-time initialization)
- **Initial Cold Prediction Latency**: $515.89\text{ ms}$
- **10x Sequential Inference Benchmark**:
  - Mean Model Inference Latency: $21.49\text{ ms}$
  - Mean Postprocessing Latency: $46.83\text{ ms}$
  - Mean Total Request Latency: $106.70\text{ ms}$
  - Latency Range: $99.05\text{ ms} - 127.75\text{ ms}$
- **GPU VRAM Utilization**:
  - Allocated VRAM: $42.80\text{ MB}$
  - Reserved VRAM: $82.00\text{ MB}$
  - VRAM Growth over 10 sequential calls: $0.00\text{ MB}$ (no GPU memory leak)

---

## 16. Numerical Sanity Tests
Evaluated on protected test events (`storm_011`, `storm_016`, `storm_007`, `storm_024`, `storm_028`):
- $H \ge 0.0\text{ m}$ everywhere (physical dry-bed constraint verified)
- Maximum simulated depth: $0.8201\text{ m}$ for `storm_011` (12 mm low storm), scaling up for extreme storms.
- Velocities finite and within physical range ($0.0 - 0.25\text{ m/s}$)
- No NaN values detected across all 24 timesteps
- No Inf values detected across all 24 timesteps

---

## 17. Regression Tests
The complete FloodWatch AI backend test suite was executed:
- `tests/test_api.py` (8 tests):
  - `test_root`: PASS
  - `test_health`: PASS
  - `test_kpis`: PASS
  - `test_forecast_risk`: PASS
  - `test_safe_route`: PASS
  - `test_alerts`: PASS
  - `test_analytics`: PASS
  - `test_system_overview`: PASS
- `tests/test_extension.py` (7 tests):
  - `test_citizen_registration`: PASS
  - `test_login_and_roles`: PASS
  - `test_otp_flow`: PASS
  - `test_rbac_restrictions`: PASS
  - `test_location_and_privacy`: PASS
  - `test_targeted_alerts`: PASS
  - `test_citizen_feedback_and_evaluation`: PASS
- `tests/test_dno_api.py` (10 tests):
  - `test_dno_health_v1`: PASS
  - `test_dno_health_direct_alias`: PASS
  - `test_dno_events_list`: PASS
  - `test_dno_prediction_valid`: PASS
  - `test_dno_prediction_with_spatial_grid`: PASS
  - `test_dno_prediction_invalid_event`: PASS
  - `test_dno_geojson_export`: PASS
  - `test_dno_geojson_validation_error`: PASS
  - `test_10x_sequential_inference_and_vram`: PASS
  - `test_cpu_fallback_execution`: PASS

**Total Test Suite Results: 25 PASSED, 0 FAILED.**

---

## 18. Production Separation
```text
+-------------------------------------------------------------------------+
|                        FLOODWATCH AI GATEWAY                            |
+-------------------------------------------------------------------------+
       |                                                 |
       v                                                 v
[PRODUCTION SUBSYSTEM]                           [EXPERIMENTAL DNO]
- Primary Risk Model: XGBoost Classifier         - Phase 7C Deep Neural Operator
- Endpoints: /forecast-risk, /safe-route         - Endpoints: /api/v1/dno/*
- Input: GCC & IMD Weather Feeds + GIS Grid      - Input: Prepared 2D Hydrodynamic Tensors
- Coverage: Greater Chennai (3,963 Sectors)      - Coverage: Adyar-Velachery Pilot (128x128)
- Operational: Active Disaster Early Warning    - Operational: Experimental Research Surrogate
```

---

## 19. Known Limitations
1. **Prepared Input Mode**: Operational real-time NWP / Doppler radar gridded rainfall forcing coupling to the 5-channel DNO tensor is not yet coupled to live station telemetry.
2. **Pilot Catchment Boundary**: The DNO model currently forecasts within the 10 km $\times$ 10 km Adyar–Velachery pilot domain ($128 \times 128$ grid), whereas production XGBoost covers 3,963 macro sectors across the entire GCC.
3. **Boundary Hydrodynamics**: Marine tidal boundary head is parameterized to 0.8 m MSL.

---

## 20. Phase 7E Recommendation
- **Status**: Backend integration and verification are **100% COMPLETE**.
- **Phase 7E Objective**: Safe integration into the Angular frontend.
- **Frontend Architecture Plan**:
  - Expose an "Experimental Hydrodynamic Forecast (Phase 7C DNO)" toggle/tab in the FloodWatch AI console.
  - Render animated 24-step depth time-series and GeoJSON inundation layers using MapLibre/Leaflet on the Adyar-Velachery pilot area.
  - Maintain clear visual demarcation between operational XGBoost alerts and experimental DNO depth simulations.
