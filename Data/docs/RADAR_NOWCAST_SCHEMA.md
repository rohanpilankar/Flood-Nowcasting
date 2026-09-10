# Doppler Weather Radar Nowcasting Interface Specification

## Scientific Status
```text
STATUS: FUTURE DATA INTERFACE
CURRENT RADAR DATA PRESENT: NO
```

> [!WARNING]
> This document defines a prospective data contract for Doppler Weather Radar (DWR) integration. **No Doppler radar observations, radar-derived precipitation rates, or radar nowcasts currently exist in this repository.**
> The current operational dataset is an offline, daily-scale spatial flood-susceptibility panel. No synthetic or simulated radar observations have been or will be fabricated.

---

## 1. Interface Overview

This schema formalizes the data structure required to ingest, preprocess, and integrate high-frequency quantitative precipitation estimates (QPE) and quantitative precipitation forecasts (QPF) from Indian Meteorological Department (IMD) or GCC Doppler Weather Radars (e.g., Chennai S-band / X-band radars) into future versions of FloodWatch AI.

---

## 2. Prospective Data Schema

Any future radar nowcast ingestion pipeline must adhere to the following columnar specification:

| Field Name | Type | Units / Format | Nullable | Description / Physical Semantics |
| :--- | :--- | :--- | :---: | :--- |
| `timestamp` | ISO 8601 Timestamp | `YYYY-MM-DDTHH:MM:SSZ` | NO | Valid forecast/observation UTC timestamp. |
| `radar_id` | String | Identifier | NO | Source radar station code (e.g., `IMD_CHENNAI_SBAND`). |
| `grid_id` | String | `CHN_G####` | NO | Spatial 500m grid cell identifier conforming to EPSG:32644. |
| `x` | Float | Meters | NO | Projected Easting coordinate in EPSG:32644 (UTM Zone 44N). |
| `y` | Float | Meters | NO | Projected Northing coordinate in EPSG:32644 (UTM Zone 44N). |
| `reflectivity_dbz` | Float | dBZ | YES | Observed radar equivalent reflectivity factor ($Z$). Range: $[-10.0, 75.0]$. |
| `rainfall_rate_mm_h` | Float | mm/h | NO | Instantaneous precipitation rate derived via Marshall-Palmer $Z = a R^b$ or polarimetric dual-pol algorithms. |
| `accumulated_rainfall_mm` | Float | mm | NO | Integrated rainfall accumulation over the forecast lead interval. |
| `quality_flag` | Integer | Enum bitmask | NO | Data quality metric (0: Uncompromised, 1: Ground clutter, 2: Beam blockage, 3: Attenuation corrected). |
| `forecast_lead_minutes` | Integer | Minutes | NO | Forecast horizon relative to origin time ($T_0$). Valid horizons defined below. |
| `source` | String | Origin name | NO | Ingestion source identifier (e.g., `IMD_DWR_RAW`, `PYSTEPS_NOWCAST`, `RAINYMOTION_V1`). |

---

## 3. Forecast Horizons & Lead Times

To fulfill true 0–3 hour nowcasting capabilities, radar nowcasting models must generate discrete lead predictions across the following horizons:

- **T+30m**: Rapid convective cell displacement and sudden cloudburst detection.
- **T+60m**: Urban subcatchment hydrologic response and surface water accumulation onset.
- **T+120m**: Macro-drain capacity thresholding and primary canal surcharging.
- **T+180m**: Basin-scale peak inflow and tidal interaction window.

---

## 4. Proposed Future Processing Frameworks

When actual radar data feeds become available, the following open-source advection and probabilistic nowcasting libraries are designated for processing:

1. **PySTEPS (Python Steps)**:
   - Extrapolation optical flow algorithms (Lucas-Kanade, VET).
   - Ensemble perturbation and spatial-temporal scale decomposition (S-PROG).
2. **Rainymotion**:
   - Optical flow models optimized for radar-based precipitation tracking (`DenseRotation`, `Sparse`).
3. **Dual-Polarimetric Algorithms**:
   - $K_{dp}$ and $Z_{dr}$ differential phase corrections for tropical monsoon convective events.

---

## 5. Compliance & Verification Rules

- **Zero Synthetic Injection**: No random or dummy rows conforming to this schema may be injected into training or validation datasets.
- **Strict Separation**: Radar nowcast features cannot be added to the offline baseline model without an audited end-to-end telemetry pipeline.
