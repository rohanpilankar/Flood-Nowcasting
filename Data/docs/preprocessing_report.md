# Chennai Urban Flood Susceptibility — Quality Control & Preprocessing Report

**Version**: 2.1 (System Alignment & Scientific Audit)  
**Date**: 2026-09-10  
**Target Variable**: `flood_occurred` (Binary 0/1)  
**Canonical Dataset**: [`chennai_flood_training.parquet`](file:///g:/fl2/Data/final/chennai_flood_training.parquet)  
**Canonical SHA-256**: `ce2bcd5766c26ec6ef152f518f73dd72facfaf00906bc4399cc6dc2c66a2c7b5`  
**Metadata Dictionary**: [`feature_columns.json`](file:///g:/fl2/Data/final/feature_columns.json)  
**Split Configuration**: [`train_test_splits.json`](file:///g:/fl2/Data/final/train_test_splits.json)  

---

## 1. System Architectural Boundary

To preserve scientific veracity across all documentation and implementations, the scope of FloodWatch AI is divided into:

### CURRENTLY IMPLEMENTED
1. **Offline Historical Dataset**: Daily panel across 32 selected dates from the 2015 Northeast Monsoon.
2. **500 m Spatial Grid**: 3,963 terrestrial grid cells in EPSG:32644 (UTM Zone 44N).
3. **Daily-Scale Observations**: Daily and cumulative rainfall interpolated via Inverse Distance Weighting (IDW) from 62 rain gauges.
4. **Event-Aware Temporal Split**: Chronologically ordered partitions isolating pre-event/first wave (TRAIN), peak onset (VAL), and subsequent deluge (TEST).
5. **XGBoost Spatial Susceptibility Baseline**: Gradient boosted trees estimating spatial susceptibility scores under daily meteorological loading.

### FUTURE COMPONENTS (FORMALLY SPECIFIED, NOT IMPLEMENTED)
1. **Doppler Radar Ingestion**: Real-time DWR reflectivity grids and QPE/QPF telemetry (see `RADAR_NOWCAST_SCHEMA.md`).
2. **0–3 Hour Rainfall Nowcasting**: High-frequency extrapolation algorithms (PySTEPS, Rainymotion).
3. **Dynamic Drainage Graph**: Manhole sensor telemetry, pipe diameters, slopes, and surcharging (see `DRAINAGE_HYDRAULIC_SCHEMA.md`).
4. **Hydraulic Coupling**: 1D/2D hydrodynamic simulation engines (EPA-SWMM, Saint-Venant).
5. **Street-Level Flood Depth**: Continuous metric water depth predictions.
6. **Real-Time GIS Routing**: Live traffic navigation avoiding inundated corridors.

---

## 2. Executive Verification Matrix

| Quality Metric | Expected / Threshold | Observed Value | Status |
| :--- | :--- | :--- | :---: |
| **Total Rows** | 126,816 | **126,816** | **PASSED** |
| **Total Columns** | 32 (6 IDs + 25 Predictors + 1 Target) | **32** | **PASSED** |
| **Audited Predictors** | Exactly 25 features | **25** | **PASSED** |
| **Null / NaN Values** | 0 across all columns | **0** | **PASSED** |
| **Infinite Values** | 0 across all numerical columns | **0** | **PASSED** |
| **Duplicate Index Rows** | 0 duplicate `[grid_id, date]` pairs | **0** | **PASSED** |
| **Coordinate System** | EPSG:32644 metric UTM grid | **EPSG:32644 (500m spacing)** | **PASSED** |
| **Unique Grid Cells** | 3,963 spatial cells | **3,963** | **PASSED** |
| **Temporal Coverage** | 32 observation dates in 2015 | **32 dates (2015-10-01 to 2015-12-10)** | **PASSED** |
| **Target Distribution** | Binary {0, 1} | **122,408 negatives (96.52%), 4,408 positives (3.48%)** | **PASSED** |
| **TRAIN Partition** | 14 dates (2015-10-01 to 2015-11-17) | **55,482 rows (1,653 positives)** | **PASSED** |
| **EXCLUDED Partition** | 8 dates (2015-11-18 to 2015-11-29) | **31,704 rows (0 positives)** | **PASSED** |
| **VALIDATION Partition** | 3 dates (2015-11-30 to 2015-12-02) | **11,889 rows (1,653 positives)** | **PASSED** |
| **TEST Partition** | 7 dates (2015-12-03 to 2015-12-10) | **27,741 rows (1,102 positives)** | **PASSED** |
| **Temporal Ordering** | max(TRAIN) < min(VAL) < min(TEST) | **2015-11-17 < 2015-11-30 < 2015-12-03** | **PASSED** |
| **Target Leakage** | 0 target-derived features in predictor set | **0 present** | **PASSED** |
| **Temporal Leakage** | No future rainfall in predictors | **0 future-derived columns** | **PASSED** |
| **Krishna Canal Feature** | Absent (`dist_to_krishna_water_canal_m`) | **Excluded from Parquet and metadata** | **PASSED** |
| **Canonical File SHA-256** | `ce2bcd5766c26ec6ef152f518f73dd72facfaf...` | **Matches canonical hash** | **PASSED** |

---

## 3. Verified Event-Aware Chronological Partitioning

| Partition | Date Range | Date Count | Rows | Positives | Negatives | Positive Rate | Role in Model Lifecycle |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **TRAIN** | 2015-10-01 to 2015-11-17 | 14 | 55,482 | 1,653 | 53,829 | 2.979% | Model parameter fitting (`scale_pos_weight = 32.564`) |
| **EXCLUDED**| 2015-11-18 to 2015-11-29 | 8 | 31,704 | 0 | 31,704 | 0.000% | Omitted buffer to eliminate post-event transition ambiguity |
| **VAL** | 2015-11-30 to 2015-12-02 | 3 | 11,889 | 1,653 | 10,236 | 13.904% | Early stopping (`eval_metric='aucpr'`) & threshold tuning |
| **TEST** | 2015-12-03 to 2015-12-10 | 7 | 27,741 | 1,102 | 26,639 | 3.972% | Frozen final one-time model evaluation |

### Spatial Overlap Disclosure
All 3,963 grid cells occur in TRAIN, VAL, and TEST:
- $\text{TRAIN} \cap \text{VAL} = 3,963$
- $\text{TRAIN} \cap \text{TEST} = 3,963$
- $\text{VAL} \cap \text{TEST} = 3,963$
This represents a city-wide temporal panel. It does not evaluate transferability to unseen geographic regions (which would require spatial block holdout).

---

## 4. Audited Predictor Inventory (25 Features)

| # | Feature Name | Physical Category | Units | Source | Temporal Semantics |
| :-: | :--- | :--- | :--- | :--- | :--- |
| 1 | `rainfall_daily_mm` | Meteorological | mm | GCC/IMD 62 gauges | Past / Current day ($t$) |
| 2 | `rainfall_cum_2d_mm` | Meteorological | mm | GCC/IMD 62 gauges | Backward 2-day sum ($t + t-1$) |
| 3 | `rainfall_cum_3d_mm` | Meteorological | mm | GCC/IMD 62 gauges | Backward 3-day sum ($t + t-1 + t-2$) |
| 4 | `rainfall_cum_7d_mm` | Meteorological | mm | GCC/IMD 62 gauges | Backward 7-day sum ($t \dots t-6$) |
| 5 | `rainfall_delta_mm` | Meteorological | mm | GCC/IMD 62 gauges | Backward difference ($t - (t-1)$) |
| 6 | `elevation_m` | Topography | m MSL | Copernicus GLO-30 | Static (DSM surface elevation) |
| 7 | `slope_deg` | Topography | degrees | Copernicus GLO-30 | Static (Gradient magnitude) |
| 8 | `low_lying_score` | Topography | $[0, 1]$ | Copernicus GLO-30 | Static (3km neighborhood depression) |
| 9 | `built_up_ratio` | Land Cover | $[0, 1]$ | ESA WorldCover 2021 | Static (Impervious fraction) |
| 10 | `water_ratio` | Land Cover | $[0, 1]$ | ESA WorldCover 2021 | Static (Surface water fraction) |
| 11 | `vegetation_ratio` | Land Cover | $[0, 1]$ | ESA WorldCover 2021 | Static (Vegetated fraction) |
| 12 | `worldcover_class` | Land Cover | Integer code | ESA WorldCover 2021 | Static (Majority modal class) |
| 13 | `soil_clay_0_5cm` | Edaphic / Soil | g/kg | ISRIC SoilGrids 2.0 | Static (Clay fraction) |
| 14 | `dist_to_swd_m` | Drainage | meters | GCC SWD 2023 GeoJSON | Static (Distance to nearest SWD) |
| 15 | `dist_to_macro_drain_m` | Drainage | meters | GCC Macro Drains GeoJSON| Static (Distance to primary drain) |
| 16 | `dist_to_micro_drain_m` | Drainage | meters | GCC Micro Drains GeoJSON| Static (Distance to secondary drain) |
| 17 | `dist_to_river_stream_m`| Drainage | meters | Basin Rivers GeoJSON | Static (Distance to Adyar/Cooum/etc.) |
| 18 | `dist_to_buckingham_canal_m`| Drainage | meters | Buckingham Canal GeoJSON| Static (Distance to canal corridor) |
| 19 | `drainage_density_m_per_km2`| Drainage | m/km² | GCC SWD 2023 GeoJSON | Static (Clipped network density) |
| 20 | `building_count` | Built Environment| count | MS Bing Footprints | Static (Footprints inside 500m cell) |
| 21 | `building_area_m2` | Built Environment| m² | MS Bing Footprints | Static (Footprint total footprint area) |
| 22 | `dist_to_hospital_m`| Infrastructure | meters | OSM Overpass API | Static (Distance to hospital/clinic) |
| 23 | `hospital_count_1km`| Infrastructure | count | OSM Overpass API | Static (Facilities within 1km) |
| 24 | `dist_to_fire_station_m`| Infrastructure| meters | OSM Overpass API | Static (Distance to fire station) |
| 25 | `dist_to_police_m` | Infrastructure | meters | OSM Overpass API | Static (Distance to police station) |
