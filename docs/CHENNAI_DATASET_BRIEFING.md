# Chennai Urban Flood Nowcasting — Dataset & Pipeline Architecture Briefing
> **System Context Document**: Copy and paste this document directly into ChatGPT or any LLM to provide full context on the repository's data assets, preprocessing pipeline, feature schema, and current machine learning state.

---

## 1. Project Overview & Objective

* **Repository**: `Flood-Nowcasting`
* **Study Area**: Greater Chennai Corporation (GCC) & Contiguous Urban Catchment, Tamil Nadu, India ($80.10^\circ - 80.35^\circ\text{ E}$, $12.85^\circ - 13.25^\circ\text{ N}$).
* **Goal**: Real-time hyper-local urban flood nowcasting using a surrogate **XGBoost classification model** operating across a **500m $\times$ 500m spatial grid**.
* **Current Status**: Data preparation and preprocessing pipeline are **100% complete**. The dataset is clean, scientifically validated, zero-leakage, has zero missing values, and is saved in production Parquet format ready for XGBoost training. (Final model training and frontend/backend integration remain to be done).

---

## 2. Directory Layout & Key Locations

```text
Flood-Nowcasting/
├── Data/
│   ├── raw/                           # Untouched raw source data
│   │   ├── Chennai rainfall.csv       # 21,416 daily telemetry records (1993-2023, 62 stations)
│   │   ├── Chennai_Copernicus_GLO30_DEM.tif # 30m Digital Elevation Model
│   │   ├── Chennai_SoilGrids_Clay_0_5cm.tif # 250m soil clay mass fraction (g/kg)
│   │   ├── Chennai_WorldCover_2021_v200.zip # 10m ESA WorldCover land use raster
│   │   ├── FloodWatch_Clean_GeoJSON.zip     # Vector drainage, canals, rivers, and 2015 flood points
│   │   ├── Chennai_Critical_Infrastructure_OSM.geojson # 1,973 hospitals, police, fire stations
│   │   ├── Chennai_Building_Footprints_Microsoft_GML_*.csv.gz # 869,486 building footprints
│   │   └── Chennai Storm Water Drains - SWD - Map 2023.kml    # (Corrupt raw KML, bypassed by clean GeoJSON)
│   ├── processed/
│   │   ├── grids/
│   │   │   ├── chennai_grid_500m.geojson  # 4,984 500m grid polygons (WGS84 EPSG:4326)
│   │   │   └── chennai_grid_500m.parquet  # 4,984 500m grid polygons (UTM 44N EPSG:32644)
│   │   ├── features/
│   │   │   ├── chennai_static_spatial_features.parquet # 4,984 cells x 26 static features
│   │   │   └── chennai_static_spatial_features.csv
│   │   ├── rasters/                   # Harmonized, projected rasters in EPSG:32644
│   │   └── vectors/                   # Reprojected, topology-validated GeoParquet layers
│   ├── final/                         # ML-Ready Training Artifacts
│   │   ├── chennai_flood_training.parquet # Primary ML Dataset (159,488 rows x 33 columns)
│   │   ├── chennai_flood_training_sample.csv # 500-row CSV inspection preview
│   │   └── feature_columns.json       # Formal feature dictionary and transformation specs
│   ├── docs/
│   │   ├── dataset_inventory.csv      # Complete audit of all 19 Chennai source layers
│   │   ├── LABEL_METHODOLOGY.md       # Ground-truth construction & leakage safeguards
│   │   └── preprocessing_report.md    # Automated quality control verification report
│   └── preprocessing/                 # Reproducible Python pipeline package
│       ├── audit.py                   # Step 1: Raw data audit & inventory
│       ├── standardize_spatial.py     # Step 2: Reprojection to UTM 44N & raster warping
│       ├── create_grid.py             # Step 3: 500m spatial grid generator
│       ├── extract_features.py        # Step 4-5: Static GIS + Dynamic IDW rainfall features
│       └── build_dataset.py           # Master end-to-end pipeline runner
├── backend/                           # FastAPI backend (endpoints for alerts, routes, flood risk)
└── Frontend/                          # Angular frontend (interactive Leaflet map and dashboards)
```

---

## 3. Spatial Grid & Coordinate Systems

* **Projected Metric CRS**: **WGS 84 / UTM Zone 44N (`EPSG:32644`)**. This is the standard projected metric system for Chennai ($\approx 13^\circ\text{ N}, 80.2^\circ\text{ E}$), enabling accurate Euclidean metric distance calculations ($m$) and area calculations ($m^2$).
* **Display / Web CRS**: **WGS 84 (`EPSG:4326`)** used for GeoJSON, latitude/longitude centroids, and Leaflet mapping.
* **Grid Resolution**: **500m $\times$ 500m cells** ($0.25\text{ km}^2$ per sector).
* **Total Spatial Sectors**: **3,963 terrestrial sectors** (`CHN_G0001` to `CHN_G3963`), spanning $12.85^\circ - 13.25^\circ\text{ N}$ and $80.10^\circ - 80.35^\circ\text{ E}$. All 1,021 deep ocean non-land cells in the Bay of Bengal have been masked out using ESA WorldCover water classifications.

---

## 4. Final ML Training Dataset Specifications

* **File**: `Data/final/chennai_flood_training.parquet`
* **File Size**: ~34 MB
* **Total Rows**: **126,816** (3,963 grid cells $\times$ 32 observation dates)
* **Total Columns**: **33** (6 Identifiers + 26 Predictor Features + 1 Binary Target)
* **Missing Values**: **0 (Zero NaNs across all columns)**
* **Duplicate Rows**: **0**

### Primary Schema Breakdown

#### A. Spatial & Temporal Identifiers (6 columns - excluded from ML feature matrix)
1. `grid_id`: Unique sector code (`CHN_G0001` to `CHN_G3963`)
2. `date`: Observation date (`YYYY-MM-DD`, spans October–December 2015)
3. `latitude`: WGS84 centroid latitude
4. `longitude`: WGS84 centroid longitude
5. `x_utm`: UTM Zone 44N easting coordinate ($m$)
6. `y_utm`: UTM Zone 44N northing coordinate ($m$)

#### B. Dynamic Meteorological Features (5 predictors)
Interpolated from 62 geocoded Greater Chennai Corporation / IMD rain gauges via Inverse Distance Weighting (IDW, power=2):
1. `rainfall_daily_mm`: Current day precipitation (0 to 340.65 mm)
2. `rainfall_cum_2d_mm`: 2-day rolling antecedent precipitation (current + 1 day prior)
3. `rainfall_cum_3d_mm`: 3-day rolling antecedent precipitation (current + 2 days prior)
4. `rainfall_cum_7d_mm`: 7-day rolling antecedent precipitation (soil moisture saturation proxy)
5. `rainfall_delta_mm`: 1-day rate of precipitation change ($\text{rain}_t - \text{rain}_{t-1}$)

#### C. Static Topography & Terrain Features (3 predictors)
Extracted from Copernicus GLO-30 Digital Surface Model (DSM, TanDEM-X radar reflection):
1. `elevation_m`: Surface elevation above Mean Sea Level (0 to 98.9 m)
2. `slope_deg`: Topographic surface gradient angle ($0^\circ$ to $35.5^\circ$)
3. `low_lying_score`: Saucer depression index measuring localized bowl depth relative to surrounding 3km neighborhood ([0, 1])

#### D. Static Land Cover & Imperviousness Features (4 predictors)
Aggregated from 10m ESA WorldCover 2021:
1. `built_up_ratio`: Fraction of cell covered by concrete/built-up structures ([0, 1])
2. `water_ratio`: Fraction of cell covered by open water bodies/wetlands ([0, 1])
3. `vegetation_ratio`: Fraction of cell covered by trees, grass, shrubs, crops ([0, 1])
4. `worldcover_class`: Dominant majority land cover integer code (50 = Built-up, 80 = Water, etc.)

#### E. Static Edaphic / Soil Feature (1 predictor)
Extracted from ISRIC SoilGrids 2.0 with spatial geological continuity interpolation for urban sealed core:
1. `soil_clay_0_5cm`: Clay particle mass fraction in topsoil 0-5 cm depth (1 to 358 g/kg).

#### F. Static Drainage Network Features (7 predictors)
Computed using Shapely `STRtree` spatial indexing over GCC storm-water drains, macro drains, micro drains, rivers, and canals:
1. `dist_to_swd_m`: Euclidean metric distance to nearest storm-water drain (m)
2. `dist_to_macro_drain_m`: Euclidean distance to nearest primary basin macro drain canal (m)
3. `dist_to_micro_drain_m`: Euclidean distance to nearest secondary micro drain feeder (m)
4. `dist_to_river_stream_m`: Euclidean distance to Adyar, Cooum, or Kosasthalaiyar river corridor (m)
5. `dist_to_buckingham_canal_m`: Euclidean distance to Buckingham Canal (m)
6. `dist_to_krishna_water_canal_m`: Euclidean distance to Krishna Water Canal (m)
7. `drainage_density_m_per_km2`: Total storm drain channel length per $km^2$ inside the 500m cell ($m/km^2$)

#### G. Static Building Footprint Features (2 predictors)
Binned from 869,486 Microsoft Bing building footprint polygons (redundant collinear density dropped):
1. `building_count`: Total building structures inside the 500m cell (0 to 978)
2. `building_area_m2`: Total ground footprint area of buildings in cell ($m^2$)

#### H. Static Critical Infrastructure Features (4 predictors)
Extracted from OpenStreetMap:
1. `dist_to_hospital_m`: Metric distance to nearest hospital or health clinic (m)
2. `hospital_count_1km`: Total hospitals/clinics within 1,000m radial buffer
3. `dist_to_fire_station_m`: Metric distance to nearest fire rescue station (m)
4. `dist_to_police_m`: Metric distance to nearest police station (m)

#### I. Target Variable (1 column)
* **`flood_occurred`**: Binary classification label ($\in \{0, 1\}$).
  * `1` (Flooded): Cell intersects ground-truth flood observations during the severe storm dates of the historic 2015 Chennai Deluge (November 15–17 and November 30 – December 4, 2015, where daily rainfall reached up to 340.8 mm).
  * `0` (Non-Flooded): Unaffected cells during the storm (presumed negatives / well-drained terrain), and all cells during dry baseline days (physically confirmed true negatives).
  * **Class Balance**: 4,408 positives (3.48%) and 122,408 negatives (96.52%). Perfect for XGBoost `scale_pos_weight` ($\approx 27.7$).

---

## 5. Strict Scientific & Leakage Safeguards

1. **No Target Leakage**: "Distance to flood points" or "historical hotspot density" were **strictly excluded** from the feature matrix. Ground truth points were used exclusively to define the `flood_occurred` label.
2. **No Future Rainfall Leakage**: Rolling rainfall metrics use backward-looking windows ($t, t-1, \dots, t-6$).
3. **No Fabricated Data**:
   * Timestamps are daily (`YYYY-MM-DD`), exactly as provided in the raw data. No fake 15-minute or hourly timestamps were manufactured.
   * Inundation depth: The raw file `Chennai_Inundation_Depth.geojson` contained 2D point coordinates with an empty attribute table. In accordance with the anti-fabrication directive, a binary classification target was constructed rather than simulating fake depth numbers.
   * Roads: Chennai OSM roads were absent from raw data; road features were excluded with proper documentation.
4. **Zero Missing Values**: Continuous spatial coverage for DEM, WorldCover, and SoilGrids (coastal water edge nodata imputed via spatial median 304.0 g/kg). Infrastructure counts cleanly evaluate to 0 in cells without structures.

---

## 6. Spatio-Temporal Validation Strategy (No Naive Random Splits)

To avoid catastrophic data leakage from spatial auto-correlation and temporal lookahead, model training must **never** use random row splitting (`train_test_split(shuffle=True)`). Instead, two validation strategies are formally specified in `Data/final/train_test_splits.json`:

1. **Chronological Event Split (Primary)**:
   - **Training Set**: 79,260 samples (October 1 to November 24, 2015; positive rate 2.09%). Captures seasonal baseflow, dry intervals, and the first major storm wave (Nov 15–17).
   - **Validation Set**: 7,926 samples (November 26 to November 29, 2015; positive rate 0.0%). Evaluates dry recession performance and threshold stability.
   - **Test Set**: 39,630 samples (November 30 to December 10, 2015; positive rate 6.95%). Evaluates the model's nowcasting ability on the unseen, historic December 1–4, 2015 catastrophic deluge.
2. **Spatial Block Cross-Validation (Regional Generalization)**:
   - **South Block** (`lat < 13.00 N`): 45,536 samples (Adyar Basin, Velachery, OMR corridor).
   - **Central Block** (`13.00 N <= lat <= 13.12 N`): 36,224 samples (Cooum Basin, GCC Core, Anna Nagar, T. Nagar).
   - **North Block** (`lat > 13.12 N`): 45,056 samples (Kosasthalaiyar Basin, Madhavaram, Puzhal, Manali).

---

## 7. How to Reproduce or Retrain

### Execution Command
The entire preprocessing workflow is automated and can be rerun from scratch with:
```powershell
.venv\Scripts\python.exe -m Data.preprocessing.build_dataset
```

### Python Dependencies Installed
* `geopandas==1.1.4`, `rasterio==1.5.1`, `shapely==2.1.2`, `pyproj==3.8.0`, `pyogrio==0.13.0`
* `pandas==3.0.5`, `numpy==2.5.3`, `scipy==1.18.1`, `pyarrow==25.0.1`, `xgboost==3.4.1`, `scikit-learn==1.9.0`
