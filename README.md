# FloodWatch AI — AI-Powered Urban Flood Nowcasting & Safe Mobility System

[![SIH Problem Statement](https://img.shields.io/badge/SIH26085-Urban%20Flood%20Nowcasting-blue.svg)](https://smartindiahackathon.gov.in/)
[![Framework - Angular 21](https://img.shields.io/badge/Frontend-Angular%2021-dd0031.svg)](https://angular.dev/)
[![Backend - FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![ML Framework - XGBoost](https://img.shields.io/badge/ML-XGBoost%20v2.0-orange.svg)](https://xgboost.readthedocs.io/)
[![Geospatial - Leaflet](https://img.shields.io/badge/GIS-Leaflet%201.9-199900.svg)](https://leafletjs.com/)
[![License - MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **SIH26085**: High-resolution 500m hyper-local flood risk nowcasting and dynamic risk-penalized shortest path safe mobility engine tailored for **Greater Mumbai (Brihanmumbai Municipal Corporation - BMC)**.

---

## 📌 Executive Summary

Urban flooding during the Southwest monsoon poses severe threats to safety, emergency mobility, and public infrastructure in low-lying coastal metropolises like Greater Mumbai ($480.24\text{ km}^2$). **FloodWatch AI** bridges the gap between traditional physics-based hydrodynamic simulations (which require hours to solve) and operational real-time emergency needs. 

By employing an **XGBoost v2.0 surrogate nowcasting classifier** trained on spatial elevation, drainage topology, hydraulic outfall distances, and rolling telemetric precipitation streams, FloodWatch AI generates sub-second flood predictions across **1,765 spatial sectors (500m × 500m grid)** with an **F1-score of 94.30%** and **ROC-AUC of 0.9997**.

Furthermore, it couples spatial hazard predictions with a **Dynamic Risk Pathfinder** (risk-penalized Dijkstra algorithm) to route commuters and emergency responders safely around submerged underpasses (e.g., Hindmata, Milan Subway, Andheri Subway) in real time.

---

## ✨ Key Features

### 1. 🌐 Hyper-Local 500m Grid Flood Nowcasting
* **Multi-Horizon Predictions**: Computes inundation probabilities for `NOW`, `+30M`, `+1H`, `+2H`, and `+3H`.
* **Spatial Granularity**: Evaluates 1,765 sectors across all 24 administrative municipal wards (A through T) in Greater Mumbai.
* **Hydro-Meteorological Features**: Incorporates 1h/3h/6h/24h rolling rainfall IDW, cloudburst acceleration ($\Delta R$), Copernicus GLO-30 DEM topography, Saucer Depression Indices, distance to drains/coast/Mithi River, and BMC 386 chronic waterlogging hotspot kernel density.

### 2. 🚦 Dynamic Safe Mobility & Hazard Routing
* **Risk-Penalized Dijkstra Graph**: Operates on an OpenStreetMap highway multigraph where edge costs dynamically adapt:
  $$\text{Edge Weight} = \text{Distance (km)} \times \left(1.0 + \left(\frac{\text{Risk Score}}{10}\right)^{2.5}\right)$$
* **Underpass Bypass Intelligence**: Automatically routes commuters onto elevated flyovers (e.g., Western Express Highway elevated corridor) while penalizing depressed saucer basins (Milan & Hindmata subways).
* **Comparative Routing Metrics**: Displays recommended safe route vs surface direct path with ETA, flood points avoided, and hazard exposure levels.

### 3. 🏛️ Dual-Role Web Portals (Angular 21 + Leaflet)
* **Regional Flood Dashboard**: Real-time municipal KPIs, rain gauge network deltas, and high-risk sector expansion alerts.
* **Interactive GIS Map**: 500m grid heatmap overlays, station telemetry markers, road status layers, and custom sector risk inspection.
* **Citizen Safety Portal**: Personalized location monitoring, SMS/OTP warning preferences, and targeted evacuation notifications.
* **BMC EOC Command Console**: Emergency incident commander dashboard with subway inundation telemetry, alert dispatch controls, and MLOps health monitoring.

---

## 📐 System Architecture

```text
                                RAW DATA INGESTION
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │  • BMC Administrative Boundary (EPSG:4326 GeoJSON)                           │
 │  • SRTM / Copernicus 30m Digital Elevation Model                             │
 │  • OpenStreetMap Roads & Stormwater Drainage Channels (Mithi, Poisar, etc.)  │
 │  • BMC 386 Chronic Waterlogging Hotspots Registry                           │
 │  • Telemetric AWS Rain Gauge Stations (60 Stations, 2024 Monsoon)            │
 └──────────────────────────────────────┬───────────────────────────────────────┘
                                        │
                                        ▼
                   GEOSPATIAL & METEOROLOGICAL PIPELINE (EPSG:32643)
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │  • Projected Metric Grid Generation (1,765 Sectors @ 500m Resolution)        │
 │  • Topographic Saucer Depression Index & Hydraulic Distance Fields           │
 │  • Spatial IDW Rainfall Interpolation & Antecedent Accumulations (1h-24h)    │
 └──────────────────────────────────────┬───────────────────────────────────────┘
                                        │
                                        ▼
                         XGBoost v2.0 SURROGATE NOWCASTER
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │  • Inference Latency: ~38.5ms                                                │
 │  • Prediction Output: Risk Level (LOW, MODERATE, HIGH, SEVERE) & Depth (m)   │
 └──────────────────────────────────────┬───────────────────────────────────────┘
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             ▼                                                     ▼
   FASTAPI REST API GATEWAY                              DYNAMIC SAFE ROUTER
 ┌───────────────────────────┐                         ┌───────────────────────┐
 │ GET /api/v1/forecast-risk │                         │ POST /api/v1/safe-    │
 │ GET /api/v1/alerts       │                         │ route                 │
 │ GET /api/v1/analytics     │                         │ (Risk-Dijkstra Path)  │
 └───────────┬───────────────┘                         └───────────┬───────────┘
             │                                                     │
             └──────────────────────────┬──────────────────────────┘
                                        │
                                        ▼
                        UNIFIED ANGULAR 21 WEB APPLICATION
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │  • Interactive GIS Map Layer (Leaflet 1.9)                                   │
 │  • Citizen Safety Portal | BMC EOC Command Console | Public Dashboard       │
 └──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Machine Learning Model Performance

Model validation was performed using a strict **chronological time-aware train/validation/test split** on monsoon storm timelines to prevent spatial-temporal data leakage:

| Model Architecture | Precision | Recall | F1-Score | ROC-AUC | PR-AUC | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression** (Linear Baseline) | 0.6842 | 0.8451 | 0.7562 | 0.8841 | 0.8466 | Benchmark |
| **Random Forest** (Nonlinear Baseline) | 0.9124 | 0.8812 | 0.8965 | 0.9620 | 0.9668 | Benchmark |
| **XGBoost Classifier** (v2.0 Production) | **0.9553** | **0.9310** | **0.9430** | **0.9997** | **0.9888** | **Production** |

### Top Feature Importances
1. `rainfall_1h`: Past 1-hour accumulated precipitation (**38.4%**)
2. `historical_hotspot_score`: Proximity to BMC chronic waterlogging underpasses (**22.1%**)
3. `elevation_m`: Absolute topographic height above MSL (**14.6%**)
4. `low_lying_score`: Relative saucer depression indicator (**9.8%**)
5. `built_up_ratio`: Impervious concrete surface fraction (**6.2%**)
6. `dist_to_drain_m`: Metric distance to nearest major storm drain (**4.5%**)
7. `rainfall_intensity_change`: Convective cloudburst acceleration factor (**2.4%**)

---

## 📁 Repository Structure

```text
Flood-Nowcasting/
├── Backend/                    # FastAPI REST API Gateway & Microservices
│   └── app/
│       ├── api/                # API routers & endpoint handlers
│       │   └── routes/         # Modular route definitions (flood, routing, alerts, analytics, etc.)
│       ├── core/               # Configuration & security settings
│       ├── db/                 # Database handlers & connection management
│       ├── schemas/            # Pydantic request & response data contracts
│       ├── services/           # Business logic, ML inference, & Dijkstra graph pathfinder
│       └── main.py             # FastAPI gateway entry point
├── Frontend/                   # Angular 21 Single Page Web Application
│   ├── src/
│   │   └── app/
│   │       ├── core/           # Auth guards, role permissions, HTTP interceptors
│   │       ├── features/       # Feature modules (dashboard, flood-map, safe-route, citizen, government, admin)
│   │       ├── shared/         # Reusable UI components & pipes
│   │       ├── app.config.ts   # Angular application configuration
│   │       └── app.routes.ts   # Route definitions & title metadata
│   ├── angular.json            # Angular CLI configuration
│   └── package.json            # NPM dependencies & build scripts
├── Data/                       # Data assets & processing pipelines
│   ├── docs/                   # Internal pipeline notes
│   ├── raw/                    # Raw boundaries, DEMs, rain station CSVs, OSM roads
│   ├── processed/              # Hydro-harmonized GeoJSON grids & distance fields
│   └── final/                  # Parquet training datasets
├── Models/                     # ML Artifacts & Metadata
│   ├── metadata/               # Metrics evaluation cards (`metrics_comparison.json`)
│   └── trained/                # Trained model binaries (`xgboost_mumbai_nowcast.json`)
├── Docs/                       # System Documentation & Specifications
│   ├── API.md                  # Comprehensive OpenAPI / REST specification
│   ├── DATA_PIPELINE.md        # Spatial ingestion & feature extraction workflow
│   ├── DATA_SOURCES.md         # Geographic & telemetry dataset inventory
│   ├── FEATURE_DICTIONARY.md   # Mathematical definitions of ML features
│   ├── LABEL_METHODOLOGY.md    # Hydrologic exceedance ground-truth rules
│   ├── LIMITATIONS.md          # Engineering constraints & Phase 3 roadmap
│   └── MODEL_CARD.md           # Model architecture & benchmark validation
└── Tests/                      # Unit & API Integration Test Suite
    ├── test_api.py             # API endpoint regression tests
    └── test_extension.py       # Services & helper utility unit tests
```

---

## 🚀 Quick Start Guide

### Prerequisites
* **Node.js**: `v20.x` or `v22.x`
* **NPM**: `v10.x`
* **Python**: `v3.10+`
* **Git**: `v2.x`

---

### 1. Frontend Setup (Angular 21)

```bash
# Navigate to Frontend directory
cd Frontend

# Install node dependencies
npm install

# Start local development server
npm start
```
> Navigate to `http://localhost:4200` in your web browser.

---

### 2. Backend Setup (FastAPI)

```bash
# Navigate to Backend directory
cd Backend

# Create a virtual environment (optional but recommended)
python -m venv venv
# Windows: venv\Scripts\activate | Linux/macOS: source venv/bin/activate

# Install required Python dependencies
pip install -r requirements.txt

# Launch FastAPI development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
> Access interactive Swagger API documentation at `http://localhost:8000/docs`.

---

### 3. Running Test Suites

```bash
# Run unit and API integration tests
pytest Tests/
```

---

## 🔌 API Endpoints Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | System liveness & ML model status |
| `GET` | `/api/v1/current-risk/kpis` | Real-time BMC municipal rainfall & risk KPIs |
| `GET` | `/api/v1/forecast-risk` | 500m grid sector predictions for specified `horizon` (`NOW`, `+30M`, `+1H`, `+2H`, `+3H`) |
| `POST` | `/api/v1/safe-route` | Dynamic risk-penalized Dijkstra path planner (Dadar $\to$ Andheri) |
| `GET` | `/api/v1/alerts` | Active emergency warnings & evacuation notices |
| `GET` | `/api/v1/analytics/summary` | Sector risk distributions & hourly rainfall curves |

For complete payload structures, query parameters, and example responses, refer to the [API Specification](file:///g:/fl2/Docs/API.md).

---

## 📚 Technical Documentation

* 📖 [API Specification (`Docs/API.md`)](file:///g:/fl2/Docs/API.md) — Complete REST endpoint documentation.
* 🛠️ [Data Pipeline Architecture (`Docs/DATA_PIPELINE.md`)](file:///g:/fl2/Docs/DATA_PIPELINE.md) — Coordinate transformations (`EPSG:32643` $\to$ `EPSG:4326`) & feature extraction.
* 📊 [Model Card (`Docs/MODEL_CARD.md`)](file:///g:/fl2/Docs/MODEL_CARD.md) — Hyperparameters, validation curves, and feature importance.
* 🗃️ [Data Sources & Provenance (`Docs/DATA_SOURCES.md`)](file:///g:/fl2/Docs/DATA_SOURCES.md) — Dataset provenance (Copernicus DEM, OSM, IMD/BMC rainfall).
* 🏷️ [Label Methodology (`Docs/LABEL_METHODOLOGY.md`)](file:///g:/fl2/Docs/LABEL_METHODOLOGY.md) — Ground-truth formulation and runoff index calculations.
* 📖 [Feature Dictionary (`Docs/FEATURE_DICTIONARY.md`)](file:///g:/fl2/Docs/FEATURE_DICTIONARY.md) — Definitions, units, and formulas for ML features.
* ⚠️ [System Limitations & Assumptions (`Docs/LIMITATIONS.md`)](file:///g:/fl2/Docs/LIMITATIONS.md) — Operational constraints & Phase 3 deployment recommendations.

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p center>
  Made for <b>Smart India Hackathon (SIH26085)</b> • Brihanmumbai Municipal Corporation (BMC) Greater Mumbai Extent
</p>
