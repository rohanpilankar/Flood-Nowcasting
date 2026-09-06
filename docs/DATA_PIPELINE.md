# Data Processing Pipeline — FloodWatch AI (Greater Mumbai)

## SIH26085 — AI-Powered Urban Flood Nowcasting & Safe Mobility System

---

## 1. Overview & Architecture

The FloodWatch AI data pipeline ingests multi-source geospatial, hydrologic, meteorological, and infrastructure data for the Brihanmumbai Municipal Corporation (BMC) Greater Mumbai extent ($480.24\text{ km}^2$), processes them through a metric projected Coordinate Reference System (**EPSG:32643**, UTM Zone 43N), extracts static and dynamic topological features, and feeds the ML inference engine and Dijkstra safe routing graph.

```text
RAW DATA INGESTION
 ├── BMC Boundary (EPSG:4326 GeoJSON)
 ├── MCGM Contours & SRTM 30m DEM
 ├── OpenStreetMap / MCGM Drainage Lines (Mithi, Poisar, Dahisar, Oshiwara)
 ├── BMC 386 Benchmark Waterlogging Hotspots Registry
 ├── Mumbai Arterial Road Network & Depressed Railway Subways
 └── BMC Telemetric AWS Hourly Rainfall Timeseries (60 stations, Monsoon 2024)
                         ↓
GEOSPATIAL HARMONIZATION (EPSG:32643 Projected CRS)
 ├── 500m Hex/Square Grid Generation (1,765 Sectors across Mumbai)
 ├── Nearest Euclidean Distance to Drains, Coast, and Mithi River
 ├── Digital Elevation Model (DEM) Sinks & Depression Saucer Index
 └── Drainage Density & Road Impervious Surface Built-up Ratio
                         ↓
METEOROLOGICAL IDW & ROLLING AGGREGATIONS
 ├── Inverse Distance Weighting (IDW, p=2.0) from Rain Gauge Network
 ├── Rolling Accumulations: R_1h, R_3h, R_6h, R_24h
 └── Intensity Delta: ΔR = R_1h - R_{prev_1h}
                         ↓
LABEL METHODOLOGY & HYDROLOGIC THRESHOLDING
 ├── Surcharge Rule: (R_1h ≥ 35mm AND Depr_Index ≥ 0.6) OR (R_3h ≥ 70mm AND Dist_Drain ≤ 300m)
 └── BMC 386 Hotspots Ground-Truth Confirmation
                         ↓
FINAL PARQUET DATASET (222,390 samples) & CHRONOLOGICAL TRAIN/TEST SPLIT
```

---

## 2. Ingestion Layers & Coordinate Reference Systems

| Layer | Source Format | Target CRS (Processing) | Target CRS (Web/API) | Output Artifact |
| :--- | :--- | :--- | :--- | :--- |
| **Boundary** | GeoJSON (WGS84) | `EPSG:32643` | `EPSG:4326` | `data/raw/boundary/mumbai_boundary.geojson` |
| **Grid** | Synthesized Poly | `EPSG:32643` | `EPSG:4326` | `data/processed/grids/mumbai_grid_500m.geojson` |
| **Drainage** | MultiLineString | `EPSG:32643` | `EPSG:4326` | `data/raw/drainage/mumbai_drains.geojson` |
| **Hotspots** | Point / Polygon | `EPSG:32643` | `EPSG:4326` | `data/raw/flood_history/mumbai_waterlogging_hotspots.geojson` |
| **Roads** | MultiLineString | `EPSG:32643` | `EPSG:4326` | `data/raw/roads/mumbai_major_roads.geojson` |
| **Rainfall** | Telemetric CSV | Station Lat/Lon | N/A | `data/raw/rainfall/mumbai_aws_rainfall.csv` |

---

## 3. Spatial Feature Engineering (`src/features/extract_spatial_features.py`)

1. **Elevation & Slope**:
   * Centroids computed in projected metric CRS (`EPSG:32643`).
   * Elevation sampled from synthesized high-resolution Mumbai topography (salient low coastal flats, central depression saucers, and eastern Trombay/Powai ridges).
   * Surface slope computed in degrees ($\theta = \arctan(\text{rise}/\text{run})$).
2. **Depression Index (Saucer Score)**:
   * Identifies concave low-lying collection bowls (Hindmata, Milan Subway, Chunabhatti, Kurla Kamani) with scores ranging from $0.05$ (ridge) to $0.98$ (depressed underpass).
3. **Hydraulic Distance Fields**:
   * Euclidean metric distance to closest municipal stormwater channel/nallah ($d_{\text{drain}}$).
   * Metric distance to the primary tidal drainage channel, the Mithi River ($d_{\text{mithi}}$).
   * Distance to western Arabian Sea / Mahim Bay coast ($d_{\text{coast}}$).
4. **Drainage Density & Built-up Impervious Ratio**:
   * Density of drainage channels per sector area ($\text{km}/\text{km}^2$).
   * Runoff imperviousness ratio ($0.45$ to $0.95$) based on urban settlement density.

---

## 4. Meteorological Temporal Ingestion (`src/features/build_ml_dataset.py`)

1. **Inverse Distance Weighting (IDW)**:
   * For each grid centroid $x$, rainfall $R(x)$ is calculated from $N=8$ key automatic weather stations:
     $$R(x) = \frac{\sum_{i=1}^N w_i R_i}{\sum_{i=1}^N w_i}, \quad w_i = \frac{1}{\max(d(x, x_i), 100)^2}$$
2. **Rolling Windows**:
   * Aggregates rolling sums over 1 hour, 3 hours, 6 hours, and 24 hours.
   * Calculates rate-of-change $\Delta R$ representing convective storm burst intensity.

---

## 5. Chronological Train / Test Validation Scheme

To prevent data leakage in time-series spatial data:
* **Training Window**: Chronological first 70% of monsoon storm events (June 1 – August 8).
* **Validation Window**: Chronological next 15% (August 9 – August 28).
* **Held-out Test Window**: Chronological final 15% (August 29 – September 15).
* Random splits are strictly prohibited to ensure true operational out-of-sample evaluation.
