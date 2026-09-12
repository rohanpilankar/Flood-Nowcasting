# CHENNAI DNO PHASE 7E: WEB INTEGRATION OF CHENNAI PHASE 7C DNO PREDICTIONS

**Document Version:** 1.0.0
**Phase:** Phase 7E
**Status:** COMPLETE & VERIFIED
**Audience:** FloodWatch AI Engineering, Hydrodynamic Modellers, GCC Emergency Command Operations

---

## 1. Objective

The objective of **Phase 7E** is to integrate the real Chennai Phase 7C Deep Neural Operator (DNO) hydrodynamic prediction model into the existing FloodWatch AI Angular frontend.

This brings real 2D spatial hydrodynamic depth ($H$) and velocity vector ($U, V$) forecasts (0–120 minutes) into the operational emergency management dashboard without replacing, disrupting, or modifying the primary production XGBoost flood risk classification pipeline, safe routing engine, or alert dispatch systems.

> **CRITICAL PHASE 7E REALITY NOTE:**
> Phase 7E uses validated prepared-event DNO inputs. It does not yet claim real-time live rainfall-to-DNO forecasting. Live radar QPE and AWS telemetry continue to feed the operational XGBoost model while the DNO operates in prepared-event hydrodynamic nowcast mode.

---

## 2. Architecture & System Boundary

The system maintains a clean decoupled architecture between the operational machine learning layer and the experimental hydrodynamic operator layer:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   FLOODWATCH AI WEB CLIENT (ANGULAR 19)                │
│                                                                        │
│  ┌───────────────────────────────┐   ┌──────────────────────────────┐  │
│  │   OPERATIONAL RISK (XGBOOST)  │   │  AI HYDRODYNAMIC NOWCAST DNO │  │
│  │   • Multi-horizon risk scores │   │  • 128x128 78m resolution    │  │
│  │   • Ward-level alerts         │   │  • Depth H (m), Vel U,V (m/s)│  │
│  │   • Safe corridor routing     │   │  • 0-120 min lead timeline   │  │
│  │   • Live weather telemetry    │   │  • Real GeoJSON spatial grid │  │
│  └───────────────▲───────────────┘   └──────────────▲───────────────┘  │
└──────────────────┼──────────────────────────────────┼──────────────────┘
                   │                                  │
       /api/v1/forecast-risk,             /api/v1/dno/health,
       /api/v1/safe-route,                /api/v1/dno/events,
       /api/v1/alerts                     /api/v1/dno/predict,
                   │                      /api/v1/dno/forecast/.../geojson
┌──────────────────▼──────────────────────────────────▼──────────────────┐
│                         FASTAPI BACKEND ENGINE                         │
│                                                                        │
│  ┌───────────────────────────────┐   ┌──────────────────────────────┐  │
│  │    XGBoost Pipeline Service   │   │     DNO Inference Service    │  │
│  │   (Tabular Risk Classifier)   │   │  (Fourier Operator Surrogate)│  │
│  └───────────────────────────────┘   └──────────────▲───────────────┘  │
└─────────────────────────────────────────────────────┼──────────────────┘
                                                      │
                       ┌──────────────────────────────▼──────────────┐
                       │           CHECKPOINT: Phase 7C α=1.00       │
                       │ SHA-256: 8c25b242b10e2bbdbee7f4a4079...     │
                       │ Native physical scale: H in m, U,V in m/s   │
                       └─────────────────────────────────────────────┘
```

---

## 3. API Integration

The Angular frontend connects directly to the FastAPI DNO endpoints via `DnoService`:

| Endpoint | Method | Purpose | Response Format |
|---|---|---|---|
| `/api/v1/dno/health` | GET | Check model load status, active hardware device (CUDA/CPU), parameter counts, checkpoint SHA-256 | `DNOHealthResponse` |
| `/api/v1/dno/events` | GET | Retrieve metadata for the 30 prepared Chennai storm events in the library | `DNOEventsResponse` |
| `/api/v1/dno/predict` | POST | Execute 24-step hydrodynamic inference for selected event | `DNOPredictResponse` |
| `/api/v1/dno/forecast/{event_id}/geojson` | GET | Export spatial grid cells as WGS84 GeoJSON polygons for Leaflet rendering | `DNOGeoJsonResponse` |

Direct aliases (`/api/dno/...`) are also exposed by the backend for backwards compatibility.

---

## 4. Angular Service Architecture (`DnoService`)

Located at `Frontend/src/app/core/services/dno.service.ts`, the service leverages Angular reactive Signals:

* `health = signal<DNOHealthResponse | null>(null)`: Live backend health and device hardware.
* `availableEvents = signal<DNOEventsResponse | null>(null)`: List of 30 storm events with precipitation stats.
* `selectedEventId = signal<string>('storm_011')`: Currently active storm scenario.
* `currentPrediction = signal<DNOPredictResponse | null>(null)`: Cached 24-step prediction payload.
* `selectedLeadMinutes = signal<number>(60)`: Currently viewed forecast horizon ($T+5$ to $T+120$).
* `isPredicting = signal<boolean>(false)`: Loading indicator state.
* `isGeoJsonLoading = signal<boolean>(false)`: GeoJSON network transmission state.
* `errorMessage = signal<string | null>(null)`: Non-blocking error alerts.

---

## 5. Dashboard Integration

The DNO interface is integrated as a dedicated section in `Frontend/src/app/features/dashboard/dashboard.component.ts`:

### Model Specification Badge
* **Model:** `Chennai Phase 7C DNO`
* **Alpha:** `1.00` (thresholded loss parameter)
* **Domain:** `Adyar–Velachery Pilot` (10 km × 10 km)
* **Resolution:** `128 × 128` (78.1 m metric grid cells)
* **Forecast Horizon:** `0–120 minutes` (24 discrete timesteps at 5-minute intervals)
* **Hardware Device:** Dynamic display (`CUDA` on NVIDIA GPU or `CPU` on fallback)

---

## 6. Event Selection & Control

The event selector dynamically populates from `GET /api/v1/dno/events`:
* Displays event ID, total precipitation (mm), duration, and rainfall category.
* Example: `storm_011 • 65.0mm (Cloudburst Convective)`.
* User triggers simulation via the **"🌊 Run Hydrodynamic Forecast"** button.
* Single prediction request caches all 24 timesteps in client memory.

---

## 7. Prediction Workflow

1. User lands on dashboard or selects an event.
2. Angular invokes `dnoService.predict({ event_id: selectedEventId, include_spatial_grids: false })`.
3. Backend runs forward pass through Fourier Operator layers on GPU (`cuda:0` ~21.5 ms).
4. Full 24-timestep physical summary ($H_{\max}$, $H_{\text{mean}}$, $V_{\max}$, threshold areas, severity bins) is returned.
5. Angular caches the forecast result.
6. Angular requests GeoJSON for current lead time ($T+60$) via `/api/v1/dno/forecast/{event_id}/geojson`.
7. Polygons are rendered onto the Leaflet map within the pilot boundary.

---

## 8. Forecast Timeline Slider (0–120 Minutes)

* **24 Timesteps:** $T+5, T+10, T+15, \dots, T+120\text{ min}$.
* **Interactive Range Slider:** Instant step scrubbing with zero GPU re-computation.
* **Step Navigation:** `◀ -5m` and `+5m ▶` micro-adjustment buttons.
* **Animation Engine:** `▶ Play Animation` / `⏸ Pause` loops through lead times every 1.5 seconds.
* **Reactive Sync:** Changing the timeline updates KPI cards, threshold areas, severity histograms, and the map layer simultaneously.

---

## 9. Key Prediction KPIs

Source of truth is strictly the backend response in native physical units:

| Metric | Symbol | Unit | Meaning |
|---|---|---|---|
| Domain Peak Water Depth | $H_{\max}$ | meters (m) | Maximum water depth across all 16,384 cells over the 120-minute horizon |
| Current Step Water Depth | $H_{\text{step}}$ | meters (m) | Maximum water depth at selected lead minute |
| Peak Velocity | $V_{\max}$ | m/s | Maximum 2D surface velocity magnitude $\sqrt{U^2 + V^2}$ |
| Flooded Footprint | Area | km² | Total area where $H > 0.05\text{ m}$ (number of wet cells $\times 6,103.5\text{ m}^2$) |
| Severe Flood Footprint | Area | km² | Total area where $H > 0.50\text{ m}$ |
| Inference Latency | Latency | ms | Exact forward operator pass execution time on GPU |

---

## 10. Depth Thresholds & Inundation Footprint

Displayed per selected timestep:
* **$> 0.05\text{ m}$ (Thin Sheet Runoff):** Early ponding and road sheen.
* **$> 0.10\text{ m}$ (Ankle-deep Water):** Pedestrian impedance.
* **$> 0.20\text{ m}$ (Curb Overtopping):** Ingress into roadside storm drains and ground-floor setbacks.
* **$> 0.50\text{ m}$ (Wheel Submersion):** Vehicle stall threshold; arterial road failure.
* **$> 1.00\text{ m}$ (Severe Submersion):** Ground-floor residential inundation; boat deployment required.

---

## 11. Depth Severity Classification Bins

Distribution across the 16,384 domain cells:
1. **Dry / Minimal:** $< 0.05\text{ m}$
2. **Low:** $0.05 - 0.10\text{ m}$
3. **Minor:** $0.10 - 0.20\text{ m}$
4. **Moderate:** $0.20 - 0.50\text{ m}$
5. **Severe:** $0.50 - 1.00\text{ m}$
6. **Very Severe:** $1.00 - 2.00\text{ m}$
7. **Extreme Deep Pooling:** $> 2.00\text{ m}$

---

## 12. Spatial Map Visualization & GIS Layers

* **Map Engine:** Leaflet with canvas hardware acceleration.
* **Layer Separation:**
  * **Operational Risk (XGBoost):** Citywide 500m GCC ward grid tiles colored by classification (Low, Medium, High).
  * **Hydrodynamic Depth (DNO):** 78.1m Adyar–Velachery pilot domain cells colored by physical depth (Cyan $\to$ Teal $\to$ Amber $\to$ Orange $\to$ Red).
* **Layer Toggling:** Dedicated GIS chip `Hydrodynamic Depth (DNO)` with online status pill.
* **Domain Focus:** Quick-action button `Focus DNO Basin (10km)` zooms to pilot bounding box `[12.943196, 80.170273] to [13.033893, 80.262192]`.
* **Interactive Tooltips:** Clicking or hovering any cell reveals:
  * Water Depth: $H\text{ (m)}$
  * Velocity Magnitude: $\sqrt{U^2 + V^2}\text{ (m/s)}$
  * Velocity Vectors: $U\text{ (m/s)}, V\text{ (m/s)}$
  * Severity category
  * Forecast lead minute

---

## 13. DNO vs Operational Model Separation

The dashboard features an architectural callout clearly communicating model roles:
* **Operational Flood Risk (XGBoost):** Primary operational model providing tabular multi-horizon classification across Greater Chennai Corporation.
* **Hydrodynamic Nowcast (Chennai Phase 7C DNO):** Advanced experimental neural surrogate solving 2D hydrodynamic equations for localized velocity and water depth.

---

## 14. Error Handling & Graceful Degradation

* Network failures, backend downtime, or invalid storm scenarios trigger a clean warning banner: `DNO hydrodynamic forecast temporarily unavailable.`
* Zero uncaught exceptions or console crash loops.
* If DNO service is offline, all existing XGBoost dashboard widgets, alerts, weather telemetry, and safe routing continue running normally without interruption.

---

## 15. Performance & Caching

* **Zero Polling:** Does not poll or repeatedly call `/predict` on UI updates.
* **Client-Side GeoJSON Caching:** Retrieved GeoJSON features for lead times are held in memory (`Map<number, any>`). Scrubbing the timeline to an already-viewed step loads in 0 ms without triggering HTTP requests.
* **Inference Speed:** DNO forward pass runs in ~21.5 ms on GPU (`cuda:0`).
* **Bundle Budget:** Angular production build strictly optimizes chunks; styles meet budget without layout shifts.

---

## 16. Verification & Test Results

### Backend Automated Test Suite
* **Command:** `python -m pytest tests/ -v`
* **Result:** **25 passed in 15.87s** (100% pass rate)
* **Endpoints verified:**
  * Root, Health, KPIs, Forecast Risk, Safe Route, Alerts, Analytics, System Overview.
  * DNO Health, DNO Events, DNO Predict Valid, DNO Predict Spatial Grids, DNO Predict Invalid Event, DNO GeoJSON Export, DNO GeoJSON Validation, 10x Sequential Inference VRAM stability, CPU Fallback.
  * Citizen registration, authentication, RBAC, targeted alerts, feedback.

### Frontend Production Build
* **Command:** `npm run build`
* **Result:** **Application bundle generation complete (0 errors)**.

---

## 17. Known Limitations & Next Steps

1. **Prepared-Event Domain:** Phase 7E DNO predictions operate on the 30 prepared Chennai storm events in the library. Real-time dynamic live rainfall coupling is reserved for Phase 8.
2. **Spatial Extent:** DNO domain covers the Adyar–Velachery 10 km × 10 km pilot basin (128 × 128 resolution). XGBoost covers all Greater Chennai Corporation zones.
3. **Physical Scale Guarantee:** Output values represent native physical units ($H\text{ in meters}$, $U,V\text{ in m/s}$). No artificial scaling or mock multipliers are applied.
