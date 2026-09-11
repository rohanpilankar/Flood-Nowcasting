# Greater Chennai Corporation (GCC) Technical Audit & DNO Feasibility Assessment
**FloodWatch AI — Urban Flood Nowcasting System**  
**Document Reference:** `docs/CHENNAI_DNO_FEASIBILITY_AUDIT.md`  
**Audit Date:** September 10, 2026  
**Target Domain:** Greater Chennai Corporation (GCC), Tamil Nadu, India  
**Target Coordinate Reference System:** EPSG:32644 (WGS 84 / UTM Zone 44N)  

---

## 1. Executive Summary

A comprehensive technical audit of the **FloodWatch AI** codebase and data assets was conducted following the migration of the target domain from Mumbai to **Greater Chennai Corporation (GCC)** (Commit `cd0b358`, current HEAD `f8da062`). The objective of this audit is to evaluate the project state, inspect all raw and processed Chennai datasets, audit the operational XGBoost spatial susceptibility baseline, and definitively assess the feasibility of training the **UrbanFloodCast Deep Neural Operator (DNO)** for Chennai.

### Key Audit Findings
1. **Repository & Git Integrity:** The repository is cleanly aligned with `origin/main` at commit `f8da062`. All code, schemas, API services, and Angular frontend views have been cleanly migrated to Greater Chennai. Zero residual Mumbai/BMC references remain in the active application code.
2. **Current Production Baseline (XGBoost):** The operational 500m grid flood susceptibility engine is fully functional. It operates on 3,963 terrestrial grid cells using 25 audited meteorological, topographical, hydrological, and infrastructural predictors. On the temporal holdout test set (Historic December 2015 Deluge, Dec 3–10, 2015), the baseline achieves a **ROC-AUC of 0.8675**, an **Optimal Threshold of 0.84**, and an **F1-Score of 0.5110**, with zero temporal data leakage across storms.
3. **Observational Flood Data Limitations:** Historical Chennai flood observations consist of 1,073 discrete point reports from the 2015 disaster (`Chennai_Flooding_Points_2015.parquet`). The file `Chennai_Inundation_Depth.parquet` contains 192 point coordinates with an empty attribute table. **No observational continuous water depth ($H$) or flow velocity ($U, V$) fields exist in the Chennai record.**
4. **Rainfall Temporal Resolution:** Raw rainfall records (`Chennai rainfall.csv`) provide 24-hour daily accumulations across 62 stations. DNO requires time-resolved rain rates $P(x, y, t)$ at 5-to-15 minute intervals.
5. **DNO Input/Target Incompatibility:** The UrbanFloodCast DNO requires spatiotemporal tensors $[B, S_y, S_x, T, T_{in}, C]$ predicting $[H, U, V]$. Because physical velocities and continuous depths do not exist in the observational datasets, the DNO **cannot** be trained directly on raw Chennai observations without fabricating data.

### Official Audit Classification
$$\mathbf{B\text{ — CHENNAI HYDRODYNAMIC DATA STILL REQUIRED}}$$

The DNO architecture cannot be trained directly on empirical observational data alone. To train a valid DNO surrogate for Greater Chennai, **a 2D hydrodynamic simulation engine (such as LISFLOOD-FP or SWMM-2D) must first be executed on Chennai's DEM and drainage network to generate physically consistent, time-resolved $H(x, y, t)$ and $U, V(x, y, t)$ training fields.**

---

## 2. Project & Git State Audit (Phase 1)

| Parameter | Observed State | Status |
| :--- | :--- | :--- |
| **Current Branch** | `main` | Verified |
| **Current Local Commit** | `f8da062b322a36b0c201a4db5ca8654ff46c0715` | Up to date |
| **Remote HEAD (`origin/main`)** | `f8da062b322a36b0c201a4db5ca8654ff46c0715` | Fully synchronized |
| **Key Migration Commit** | `cd0b358` (`feat: complete Greater Chennai Corporation (GCC) migration for FloodWatch AI`) | Present in history |
| **Working Tree State** | Clean (untracked research directories: `External/`, temporary: `scratch/`) | Safe |
| **Git Stashes** | `stash@{0}: On main: backup before Chennai migration pull` | Preserved (untouched) |
| **Code Modification Rules** | No stash-pop, no resets, no modifications to `External/UrbanFloodCast/` | Strictly enforced |

---

## 3. Chennai Data Inventory (Phase 2)

```
Data/
├── raw/
│   └── Chennai rainfall.csv                         [21,416 rows, 62 stations, Daily 1993-2021]
├── processed/
│   ├── features/
│   │   └── chennai_static_spatial_features.parquet  [3,963 rows x 24 cols, 500m grid features]
│   ├── grids/
│   │   ├── chennai_grid_500m.geojson                [3,963 polygons, EPSG:4326 / WGS84]
│   │   └── chennai_grid_500m.parquet                [3,963 polygons, EPSG:32644 / UTM 44N]
│   ├── rasters/
│   │   ├── chennai_dem_30m_utm44n.tif               [3987 x 3332, 30m resolution, EPSG:32644]
│   │   ├── chennai_soil_clay_250m_utm44n.tif        [479 x 401, 250m resolution, EPSG:32644]
│   └── vectors/
│       ├── Chennai_Flooding_Points_2015.parquet     [1,073 point reports, EPSG:32644]
│       ├── Chennai_Inundation_Depth.parquet         [192 point coordinates, empty attributes]
│       ├── Chennai_Storm_Water_Drains_2023.parquet  [10,958 lines, EPSG:32644]
│       ├── Chennai_Basin_Macro_Drains.parquet       [18 lines, EPSG:32644]
│       ├── Chennai_Basin_Micro_Drains.parquet       [610 lines, EPSG:32644]
│       ├── Chennai_Basin_Rivers_Streams.parquet     [4 lines: Adyar, Cooum, Kosasthalaiyar, Otteri]
│       ├── Chennai_Buckingham_Canal.parquet         [4 lines, EPSG:32644]
│       └── Chennai_Krishna_Water_Canal.parquet      [2 lines, EPSG:32644]
└── final/
    ├── chennai_flood_training.parquet               [126,816 rows x 33 cols, 500m panel 2015]
    ├── chennai_flood_training_sample.csv            [100 rows preview]
    ├── feature_columns.json                         [25 audited predictor names]
    └── train_test_splits.json                       [Event-blocked temporal split configuration]
```

### 3.1 Rainfall Assessment (`Data/raw/Chennai rainfall.csv`)
* **Row Count:** 21,416 rows.
* **Columns:** `Station_Names` (string), `Dates` (string `DD-MM-YYYY`), `Rainfall` (float64).
* **Temporal Range:** January 1, 1993 to December 31, 2021 (29 years).
* **Temporal Resolution:** **24-hour daily cumulative total**.
* **Spatial Resolution:** 62 nominal rain gauge stations across the Chennai Metropolitan Area. Station geographic coordinates are not embedded in this raw CSV.
* **Missing Values:** 0 null values. Maximum recorded single-day rainfall: 494.0 mm.
* **Nowcasting Suitability:** **Unsuitable for direct DNO nowcasting.** Hydrodynamic wave routing and DNO forward operators require fine-grained boundary conditions (e.g. 5, 10, or 15-minute precipitation steps $\Delta t$) to compute runoff and overland inundation progression. Daily cumulative values are suitable for macro-scale machine learning susceptibility classification, but cannot capture sub-hourly flash flooding hydrodynamics.

### 3.2 Flood Labels Assessment
* **`Chennai_Flooding_Points_2015.parquet`:**
  * Rows: 1,073 point locations.
  * Columns: `name` (string), `geometry` (Point, EPSG:32644).
  * Timestamps: None. Represents aggregate inundation complaints/field reports during the November–December 2015 disaster.
  * Water Depth: None recorded.
* **`Chennai_Inundation_Depth.parquet`:**
  * Rows: 192 point locations.
  * Columns: `geometry` (Point, EPSG:32644) only.
  * Attribute Table: Empty (no depth, no velocity, no timestamp, no station name).
* **Ground Truth Verification:**
  * **Continuous depth fields $H(x, y, t)$:** MISSING.
  * **Continuous velocity fields $U(x, y, t), V(x, y, t)$:** MISSING.
  * **Conclusion:** These datasets represent **sparse binary presence/absence indicators** for historical calibration. They **cannot** be treated as continuous physical ground truth.

---

## 4. Final ML Dataset & Data Leakage Audit (Phase 3)

### 4.1 Dataset Structure (`Data/final/chennai_flood_training.parquet`)
* **Shape:** 126,816 rows $\times$ 33 columns.
* **Constituency:** Spatiotemporal Cartesian product of **3,963 spatial grid cells** $\times$ **32 daily timestamps** during the 2015 Northeast Monsoon (2015-10-01 to 2015-12-10).
* **Target Variable:** `flood_occurred` (binary $\{0, 1\}$).
  * Positive instances: 4,408 (3.48%).
  * Negative instances: 122,408 (96.52%).
  * Extreme class imbalance: 1:28 ratio.
* **Missing Values:** 0 missing values across all columns.

### 4.2 Feature Architecture (25 Audited Predictors)
1. **Dynamic Meteorology (5):** `rainfall_daily_mm`, `rainfall_cum_2d_mm`, `rainfall_cum_3d_mm`, `rainfall_cum_7d_mm`, `rainfall_delta_mm`.
2. **Topography & Terrain (3):** `elevation_m` (DEM), `slope_deg`, `low_lying_score` (relative topographic sink depression).
3. **Surface & Soil Properties (5):** `built_up_ratio` (imperviousness), `water_ratio`, `vegetation_ratio`, `worldcover_class`, `soil_clay_0_5cm` (retention proxy).
4. **Drainage Proximity & Density (6):** `dist_to_swd_m`, `dist_to_macro_drain_m`, `dist_to_micro_drain_m`, `dist_to_river_stream_m`, `dist_to_buckingham_canal_m`, `drainage_density_m_per_km2`.
5. **Urban Infrastructure Exposure (6):** `building_count`, `building_area_m2`, `dist_to_hospital_m`, `hospital_count_1km`, `dist_to_fire_station_m`, `dist_to_police_m`.

### 4.3 Partitioning & Data Leakage Audit (`train_test_splits.json`)

```
2015-10-01                               2015-11-17        2015-11-30   2015-12-02   2015-12-03        2015-12-10
[================== TRAIN SET ===================] [BUFFER] [=== VALIDATION ===] [========== TEST SET ==========]
      67,371 rows (17 days, 1,747 floods)            12 days   11,889 rows (3 days)   31,704 rows (8 days, 1,678 fl)
```

* **Methodology:** **Event-Blocked Temporal Split**.
  * **Train:** Oct 1 – Nov 17, 2015 (includes initial monsoon showers and the first major flood peak on Nov 15–17).
  * **Buffer Exclusion Zone:** Nov 18 – Nov 29, 2015 (12 dates excluded completely to prevent serial correlation and hydrological bleed-through between storms).
  * **Validation:** Nov 30 – Dec 02, 2015 (storm ramp-up period).
  * **Test:** Dec 03 – Dec 10, 2015 (historic deluge peak and recession).
* **Leakage Assessment:**
  * **Temporal Leakage:** **NONE.** Future observations are never visible to the training split, and the 12-day buffer prevents lag leakage from autoregressive rainfall features (`rainfall_cum_7d_mm`).
  * **Spatial Overlap:** All 3,963 grid cells exist across train, validation, and test splits. This setup evaluates the model's ability to predict **unseen extreme meteorological events over a fixed spatial territory**, rather than spatial out-of-domain extrapolation.

---

## 5. Spatial Data & Raster Audit (Phase 4)

| Dataset | Type | CRS | Dimensions / Count | Resolution | Extent / Bounds |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `chennai_grid_500m.parquet` | Vector Polygons | EPSG:32644 | 3,963 cells | 500m $\times$ 500m | `[402000, 1420500, 428500, 1465000]` |
| `chennai_dem_30m_utm44n.tif` | GeoTIFF Raster | EPSG:32644 | $3,987 \times 3,332$ px | 30.0 m | `[388485, 1400265, 488445, 1519875]` |
| `chennai_soil_clay_250m_utm44n.tif`| GeoTIFF Raster | EPSG:32644 | $479 \times 401$ px | 250.0 m | `[388375, 1400125, 488625, 1519875]` |
| `chennai_worldcover_10m_utm44n.tif`| GeoTIFF Raster | EPSG:32644 | $3,813 \times 5,542$ px | 10.0 m | `[373400, 1409740, 428820, 1447870]` |

### Spatial Observations
1. **Grid Regularity:** The 500m grid is generated from a regular Cartesian lattice ($53 \times 89$ cells in UTM Zone 44N), but clipped to the terrestrial administrative boundary of Greater Chennai, resulting in 3,963 active land cells.
2. **DEM Quality:** Elevation ranges from 0.0 m (Bay of Bengal coast) to 98.9 m (inland ridges), with a median of 13.9 m and mean of 17.5 m, accurately reflecting Chennai's flat coastal plain topography.
3. **Resampling Alignment:** For any future 2D hydrodynamic solver or neural operator grid, these rasters must be resampled to a unified grid resolution (e.g. 30m or 100m) over the common bounding box.

---

## 6. Drainage Infrastructure Audit (Phase 5)

Detailed inspection of the vector layers in `Data/processed/vectors/` and `Data/docs/DRAINAGE_HYDRAULIC_SCHEMA.md` reveals:

```
+-----------------------------------------+--------+-----------------+----------------------------------------+
| Layer Name                              | Lines  | Geometry        | Available GIS Attributes               |
+-----------------------------------------+--------+-----------------+----------------------------------------+
| Chennai_Storm_Water_Drains_2023.parquet | 10,958 | LineString 2D   | Name, length, ward, type               |
| Chennai_Basin_Macro_Drains.parquet      |     18 | LineString 2D   | Basin name, channel length             |
| Chennai_Basin_Micro_Drains.parquet      |    610 | LineString 2D   | Channel ID, length, zone               |
| Chennai_Basin_Rivers_Streams.parquet    |      4 | LineString 2D   | Adyar, Cooum, Kosasthalaiyar, Otteri   |
| Chennai_Buckingham_Canal.parquet        |      4 | LineString 2D   | Reach name, corridor length            |
| Chennai_Krishna_Water_Canal.parquet     |      2 | LineString 2D   | Section name, length                   |
+-----------------------------------------+--------+-----------------+----------------------------------------+
```

### Available vs. Missing Hydraulic Parameters

| Parameter | Availability Status | Notes |
| :--- | :--- | :--- |
| **Spatial 2D Alignment** | **AVAILABLE** | Complete geographic alignment in EPSG:32644 |
| **Channel / Conduit Length** | **AVAILABLE** | Accurately derived from GIS geometries |
| **Invert Elevations ($Z_{in}, Z_{out}$)** | **MISSING** | No underground pipe invert levels in GIS layers |
| **Pipe Diameters & Dimensions** | **MISSING** | Only qualitative labels ("macro", "micro") exist |
| **Conduit Cross-Section Shape** | **MISSING** | Box vs circular vs open trapezoidal not recorded |
| **Flow Direction Vectors** | **MISSING** | Digitized lines do not guarantee hydraulic direction |
| **Live Telemetric Depth / Flow** | **MISSING** | No live IoT telemetry feeds on SWD conduits |

> [!IMPORTANT]
> The static GIS layers provide excellent spatial proximity and density metrics for tabular machine learning models. However, they **do not constitute a 1D/2D hydraulic network model** (such as EPA SWMM) due to missing invert elevations, diameters, and boundary conditions.

---

## 7. Existing XGBoost Baseline Model Audit (Phase 8)

* **Artifacts:**
  * Model binary: `models/trained/chennai_xgboost_baseline.json`
  * Metadata: `models/metadata/chennai_xgboost_baseline_metadata.json`
  * Evaluation metrics: `models/metadata/chennai_xgboost_baseline_metrics.json`
  * Feature importance: `models/metadata/chennai_xgboost_baseline_feature_importance.json`
* **Model Objective:** Spatial flood susceptibility prediction (binary classification of sector inundation likelihood).
* **Test Performance (Dec 3–10, 2015 Deluge):**
  * **ROC-AUC:** $0.8675$
  * **PR-AUC:** $0.4247$
  * **Optimal Decision Threshold:** $0.8400$
  * **Precision (at 0.84):** $0.3809$
  * **Recall (at 0.84):** $0.7765$
  * **F1-Score (at 0.84):** $0.5110$

### Top Feature Importances (XGBoost Gain)
1. `rainfall_cum_7d_mm` ($27.3\%$) — Soil saturation & antecedent moisture accumulation.
2. `dist_to_swd_m` ($14.7\%$) — Proximity to municipal storm drainage outfalls.
3. `rainfall_cum_3d_mm` ($13.8\%$) — Medium-term storm surge intensity.
4. `drainage_density_m_per_km2` ($9.1\%$) — Local drainage capacity and coverage.
5. `elevation_m` ($6.2\%$) — Low-lying topographic depression susceptibility.

### Model Distinction: XGBoost vs. DNO
| Dimension | XGBoost Baseline (Operational) | UrbanFloodCast DNO (Research Target) |
| :--- | :--- | :--- |
| **Model Type** | Gradient Boosted Decision Trees | Fourier / Neural Operator PDE Surrogate |
| **Target Variable** | Binary Susceptibility Probability $[0, 1]$ | Continuous Fields: $H(x,y,t)$, $U(x,y,t)$, $V(x,y,t)$ |
| **Spatial Output** | 3,963 discrete 500m vector grid sectors | Continuous 2D raster field ($128 \times 128$) |
| **Temporal Step** | Daily / Event cumulative step | Sub-hourly hydrodynamic time steps ($\Delta t = 5\text{–}15\text{ min}$) |
| **Governing Laws** | Statistical feature association | 2D Shallow Water Equations (SWE) |
| **Production Ready** | **YES** (Operational in Backend/Frontend) | **NO** (Requires simulated training data) |

---

## 8. UrbanFloodCast DNO Compatibility Matrix (Phase 6 & 7)

The original UrbanFloodCast DNO maps input tensors $a \in \mathbb{R}^{B \times S_y \times S_x \times T \times T_{in} \times C_{in}}$ to target hydrodynamic states $u \in \mathbb{R}^{B \times S_y \times S_x \times T \times C_{out}}$.

| Variable | Physical Meaning | Available in Chennai? | Data Source / Reason |
| :---: | :--- | :---: | :--- |
| $H_0$ | Initial water depth field | **NO** | No pre-storm surface water depth rasters exist |
| $U_0$ | Initial $X$-velocity field | **NO** | Overland flow velocity is not measured by telemetry |
| $V_0$ | Initial $Y$-velocity field | **NO** | Overland flow velocity is not measured by telemetry |
| $P(t)$ | Spatiotemporal rain rate | **PARTIAL** | Daily totals exist; 5-min DWR radar grids missing |
| $Z$ | Digital Elevation Model | **YES** | `chennai_dem_30m_utm44n.tif` (High quality 30m DEM) |
| **Target $H$** | Continuous water depth field | **NO** | Only discrete binary presence points exist |
| **Target $U$** | Continuous $X$-velocity field | **NO** | No 2D velocity observations exist |
| **Target $V$** | Continuous $Y$-velocity field | **NO** | No 2D velocity observations exist |

### Detailed DNO Evaluation Questions
1. **Do we have $H_0, U_0, V_0$?** No. Surface velocity and initial depth fields are absent.
2. **Do we have precipitation $P$?** Only daily point station data. Not the continuous dynamic field required by DNO.
3. **Do we have DEM $Z$?** Yes.
4. **Do we have target $H, U, V$?** No. Neither continuous water depth nor 2D flow velocities are observed.
5. **Do we have enough time-resolved storm events?** No. Observational data contains only daily aggregates for 2015.
6. **Can data be mapped to regular 2D spatial grid?** Spatial features can, but dynamic targets cannot without simulation.
7. **Can we construct tensor $[B, S_y, S_x, T, T_{in}, C]$ without data fabrication?** **NO.** Fabricating velocities or setting them to zero would corrupt the Navier-Stokes / Shallow Water physics that the DNO operator is designed to learn.

---

## 9. Backend & Frontend Architecture Audit (Phase 9)

### 9.1 Backend Services Inspection
* `backend/app/services/flood_service.py`:
  * Implements vectorized inference across 3,963 grid sectors using `chennai_xgboost_baseline.json`.
  * **Zero-Fabrication Guarantees:** Returns `"waterDepth": None` to explicitly state that continuous water depth is unmeasured. Future prediction horizons (`+30M`, `+1H`, etc.) return an explicit `forecast_data_unavailable` state rather than multiplying numbers by arbitrary fudge factors.
* `backend/app/services/drainage_graph_service.py`:
  * Builds a 3D arterial corridor graph (18 key nodes, 14 major reaches) spanning the Adyar, Cooum, and Kosasthalaiyar basins and Buckingham Canal. Uses Manning's equation and Rational runoff for hydraulic capacity estimation along trunk corridors.
* `backend/app/services/rainfall_service.py`:
  * Connects to IMD Chennai telemetry and S-band Doppler Weather Radar (DWR) station metadata.
* **Import Validation:** Executed `scratch/test_backend_imports.py`. All backend modules, models, schemas, and services load cleanly in 1.4s with 0 errors.

### 9.2 Frontend Audit
* **Framework:** Angular 19 (Standalone Components, TypeScript).
* **Build Validation:** Executed `npm run build` in `Frontend/`. Output generated in 17.8s with **0 compilation errors**.
* **Simulation Studio (`features/simulation/`):** Accurately labeled as "XGBoost Flood Susceptibility Simulation Studio". Allows users to vary 24-hour rainfall, 3-day cumulative rainfall, rainfall delta, and coastal tidal lock penalties to simulate GCC-wide sector risk.
* **Residual String Check:** Full grep of `backend/` and `Frontend/` confirmed **0 occurrences of "Mumbai" or "BMC"**.

---

## 10. Technical Validation Summary (Phase 10)

| Test Item | Command / Procedure | Result | Notes |
| :--- | :--- | :--- | :--- |
| **Git Status Check** | `git status` | Clean | `f8da062` HEAD confirmed |
| **Backend Imports** | `python scratch/test_backend_imports.py` | **PASSED** | All 4 services initialized |
| **XGBoost Inference** | Direct DMatrix load & predict | **PASSED** | 3,963 sectors evaluated in 32ms |
| **Vector Integrity** | GeoPandas CRS & schema audit | **PASSED** | All 8 vector layers verified |
| **Raster Integrity** | Rasterio bounds, NoData, stats | **PASSED** | DEM, clay, worldcover verified |
| **Frontend Compilation**| `npm run build` | **PASSED** | Production bundle generated |

---

## 11. Recommended System Architecture

```
                                    +-----------------------------------------------+
                                    |     FloodWatch AI Operational Platform        |
                                    +-----------------------------------------------+
                                                           |
                      +------------------------------------+------------------------------------+
                      |                                                                         |
                      v                                                                         v
+-------------------------------------------+             +-------------------------------------------------------------+
|    TIER 1: Operational Baseline (ACTIVE)  |             |     TIER 2: Hydrodynamic DNO Research Pipeline (FUTURE)     |
+-------------------------------------------+             +-------------------------------------------------------------+
| * Model: XGBoost Spatial Classifier       |             | * Step 1: Hydrodynamic Simulation (LISFLOOD-FP / SWMM-2D)   |
| * Domain: 3,963 Grid Cells (500m)         |             |   - Input: Chennai 30m DEM + Sub-hourly Rain Time Series    |
| * Target: Inundation Susceptibility [0,1] |             |   - Output: Synthetic Ground Truth H(x,y,t), U(x,y,t), V    |
| * Status: Production Ready, <50ms latency |             | * Step 2: DNO Operator Training                             |
| * Serves: EOC Dashboard, Simulation Studio|             |   - Architecture: Fourier Neural Operator (FNO-3D / DNO)   |
+-------------------------------------------+             |   - Target: Sub-second 2D Water Depth & Velocity Surrogate  |
                                                          | * Status: Blocked until hydrodynamic simulation is executed |
                                                          +-------------------------------------------------------------+
```

### Next Datasets Required for DNO Feasibility
1. **Sub-Hourly Rainfall Hyetographs:** 15-minute precipitation timeseries for major Chennai rainfall events (e.g. Cyclone Michaung 2023, Cyclone Vardah 2016, November 2015).
2. **Hydrodynamic Simulation Engine:** A calibrated 2D hydraulic solver (such as **LISFLOOD-FP** or **Telemac-2D**) run over Chennai's 30m DEM to produce continuous ground truth grids:
   $$H(x, y, t) \in \mathbb{R}^{S_y \times S_x \times T}, \quad U(x, y, t) \in \mathbb{R}^{S_y \times S_x \times T}, \quad V(x, y, t) \in \mathbb{R}^{S_y \times S_x \times T}$$
3. **Tidal & Coastal Boundary Conditions:** Water levels at the mouths of the Adyar, Cooum, and Buckingham Canal outfalls during high tide / storm surge conditions.

---

## 12. Risks and Limitations

1. **Risk of Misrepresenting Simulated Data as Real:** Continuous depth fields generated by hydraulic models must always be clearly marked as `SIMULATED HYDRODYNAMIC TRAINING DATA`. They must never be represented to emergency agencies as sensor-verified field measurements.
2. **Single-Disaster Historical Calibration:** The existing XGBoost baseline is heavily anchored on the 2015 Northeast Monsoon disaster records. Performance on convective summer cloudbursts or non-monsoonal infrastructure failures may exhibit higher variance.
3. **GPU VRAM Constraints for 2D DNO:** If DNO training is pursued with simulated hydrodynamic data, the developer environment (NVIDIA RTX 3050 Laptop GPU, 6GB VRAM) requires spatial patch cropping ($128 \times 128$ or $64 \times 64$) with batch size 1 and mixed precision (`torch.cuda.amp.autocast`) to avoid CUDA Out-Of-Memory errors.

---

## 13. Official Final Classification

$$\Huge\mathbf{B}$$
### **B — CHENNAI HYDRODYNAMIC DATA STILL REQUIRED**

**Formal Justification:**  
The repository successfully maintains a validated, production-ready XGBoost baseline for Greater Chennai Corporation. However, the observational record lacks time-resolved continuous flood depth ($H$) and overland flow velocity fields ($U, V$). Training the UrbanFloodCast Deep Neural Operator (DNO) without continuous physical fields would require fabricating data or assigning arbitrary zero values, violating fundamental fluid dynamics. Therefore, **experimental DNO training cannot begin until a physically based 2D hydrodynamic simulation pipeline produces calibrated Chennai training targets.**

---

## 14. Recommended Next-Step Plan

1. **Preserve Operational Baseline:** Keep `models/trained/chennai_xgboost_baseline.json` as the operational nowcasting engine powering the FastAPI backend and Angular dashboard.
2. **Isolate DNO in Research Pipeline:** Maintain all neural operator development strictly within `models/urban_flood_dno/` as an experimental track.
3. **Formulate Chennai Hydrodynamic Simulation POC:**
   - Define a focused $10\text{ km} \times 10\text{ km}$ pilot sector within Greater Chennai (e.g., the Velachery–Adyar Basin).
   - Prepare a 30m raster grid with DEM and Manning's roughness.
   - Run a 2D shallow water hydrodynamic simulation (e.g. LISFLOOD-FP) driven by a synthetic or historical sub-hourly hyetograph.
   - Export physical $H, U, V$ tensors and evaluate DNO forward-backward convergence on the RTX 3050 GPU.
