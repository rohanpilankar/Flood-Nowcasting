# Chennai Urban Flood Ground-Truth & Target Labeling Methodology

**Version**: 2.1 (Scientific Alignment)  
**Correction Date**: 2026-09-10  
**Status**: SCIENTIFICALLY VALIDATED & AUDITED

---

## 1. Primary Objective

The goal is to construct a scientifically valid, binary flood occurrence target (`flood_occurred` $\in \{0, 1\}$) across a 500m $\times$ 500m spatial grid coupled with daily hydro-meteorological timelines, without synthetic data, fake timestamps, or target leakage.

---

## 2. Scientific Scope: Implemented vs. Future Architecture

To maintain strict scientific integrity, the boundary between what the data supports and what future versions intend to achieve is explicitly delineated:

### CURRENTLY IMPLEMENTED
- **Offline Historical Dataset**: Daily observations across 32 selected dates from the 2015 Northeast Monsoon season.
- **500 m Spatial Grid**: Metric grid (EPSG:32644) covering 3,963 terrestrial Chennai cells.
- **Daily-Scale Observations**: Backward-looking daily rainfall accumulations derived from 62 rain gauges.
- **Event-Aware Temporal Split**: Chronological partitioning preserving physical storm progression.
- **XGBoost Spatial Susceptibility Baseline**: Gradient boosted decision tree classifying cell-level spatial susceptibility under high rainfall loading.

### FUTURE COMPONENTS (NOT IMPLEMENTED)
- **Doppler Radar Ingestion**: Real-time DWR reflectivity and QPE/QPF feeds (see `RADAR_NOWCAST_SCHEMA.md`).
- **0–3 Hour Rainfall Nowcasting**: High-frequency extrapolation (e.g., PySTEPS, Rainymotion).
- **Dynamic Drainage Graph**: Manhole telemetry, conduit cross-sections, and hydraulic capacities (see `DRAINAGE_HYDRAULIC_SCHEMA.md`).
- **Hydraulic Coupling**: 1D/2D hydrodynamic solvers (SWMM, Saint-Venant, shallow-water equations).
- **Street-Level Flood Depth**: Metric continuous water-depth measurements.
- **Real-Time GIS & Flood-Safe Routing**: Live telemetry dispatch and street hazard navigation.

---

## 3. Source Datasets & Ground-Truth Verification

The target labels are derived from two real-world geospatial observation datasets provided in `Data/raw/FloodWatch_Clean_GeoJSON.zip`:

### A. 2015 Historic Flood Disaster Inundation Points (`Chennai_Flooding_Points_2015.geojson`)
- **Total Features**: 753 point locations.
- **Event Period**: Historic North-East Monsoon Deluge (November 15 – December 4, 2015).
- **Physical Context**: On December 1–2, 2015, Chennai recorded up to 340.8 mm of rainfall in 24 hours (Chennai Airport / Meenambakkam: 340.8 mm; Ambattur: 292.0 mm; Nungambakkam: 291.5 mm). This resulted in catastrophic urban flooding, inundation of the Adyar and Cooum river corridors, Buckingham canal overflow, and severe street-level waterlogging.
- **Geographic Coverage**: Spans central Chennai, Adyar, Velachery, Tambaram, Ambattur, Anna Nagar, Kolathur, and North Chennai (Tondiarpet, Royapuram).

### B. Chronic Urban Inundation Points (`Chennai_Inundation_Depth.geojson`)
- **Total Features**: 192 point locations.
- **Geometry Type**: 2D Point coordinates (`[longitude, latitude]`).
- **Depth Attribute Audit**: Inspection of the GeoJSON reveals that the properties dictionary is empty (`{}`) and coordinates are 2D with no third coordinate for depth.
- **Decision on Continuous Depth Target**: In strict accordance with the project rules (*"If the data only supports binary flood occurrence, create a binary flood target. Do not invent observations"*), we do **not** invent or synthesize numerical depth measurements. The data supports binary flood occurrence, so `flood_occurred` is defined as a binary classification target.

---

## 4. Spatial & Temporal Label Construction

### Spatial Association
- Each 500m $\times$ 500m grid cell polygon in `EPSG:32644` is intersected with the 945 real observed flood and inundation locations (753 2015 points + 192 inundation points).
- Grid cells that contain or are directly intersected by ground-truth flood points are classified as flood-susceptible locations during high-impact rainfall events.
- **Spatially mapped cells**: 551 unique 500m cells out of 3,963 total (13.9% of cells have any flood ground-truth).

### Temporal Association
- Flooding is an episodic hazard triggered by extreme hydrologic loading on low-lying terrain and saturated drainage networks.
- **Active Flood Dates (8 dates total)**:
  - First Wave: November 15, November 16, November 17, 2015.
  - Second Peak Deluge: November 30, December 1, December 2, December 3, December 4, 2015.
- During these 8 peak flood disaster dates:
  - Cells intersecting ground-truth flood observations are labeled `flood_occurred = 1` ($551 \times 8 = 4,408$ positive observations).
  - Cells outside the inundation footprint are labeled `flood_occurred = 0` (presumed negatives / well-drained terrain).
- **Non-Flood Baseline Dates (24 dates total)**:
  - During dry days and low/moderate rainfall days (e.g. October dry spells, post-event recession periods), even susceptible low-lying cells did not inundate.
  - All cells on non-flood days are labeled `flood_occurred = 0` (physically confirmed true negatives).

---

## 5. Event-Aware Chronological Partitioning

The dataset is partitioned deterministically according to event boundaries:

| Split | Date Range | Dates | Rows | Positives | Negatives | Pos. Rate |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **TRAIN** | 2015-10-01 → 2015-11-17 | 14 | 55,482 | 1,653 | 53,829 | 2.98% |
| **EXCLUDED** | 2015-11-18 → 2015-11-29 | 8 | 31,704 | 0 | 31,704 | 0.00% |
| **VALIDATION**| 2015-11-30 → 2015-12-02 | 3 | 11,889 | 1,653 | 10,236 | 13.90% |
| **TEST** | 2015-12-03 → 2015-12-10 | 7 | 27,741 | 1,102 | 26,639 | 3.97% |

### Temporal Integrity
$$\max(\text{TRAIN date}) < \min(\text{VALIDATION date}) \quad \text{and} \quad \max(\text{VALIDATION date}) < \min(\text{TEST date})$$
- `2015-11-17 < 2015-11-30` (EXCLUDED window 2015-11-18 to 2015-11-29 acts as buffer).
- `2015-12-02 < 2015-12-03`.

### Spatial Overlap Disclosure
- Across TRAIN, VALIDATION, and TEST, exactly the same 3,963 grid cells are present:
  $$\text{TRAIN} \cap \text{VAL} = \text{TRAIN} \cap \text{TEST} = \text{VAL} \cap \text{TEST} = 3,963$$
- This spatial overlap is characteristic of an offline temporal panel where fixed spatial entities are monitored over time. It is not an accidental data error; however, users must understand that the model is evaluated on future temporal slices of known spatial grid cells, rather than under strict spatial holdout.

---

## 6. Scientific Limitations & Boundaries

1. **Forward-in-Time Extrapolation within Same Season**: The validation and test periods are portions of the same broader second flood episode (late November / early December 2015). The evaluation represents forward-in-time extrapolation on a later phase of this disaster, not independent generalization to a completely distinct unobserved flood season.
2. **Positive-Unlabeled (PU) Presumed Negatives**: Presumed negatives on active flood days reflect unrecorded cells. Reporting bias towards densely populated areas may cause some flooded rural/fringe cells to be marked as 0.
3. **Copernicus GLO-30 DSM**: Elevation reflects surface canopy and structure tops rather than bare-earth terrain.
4. **Static WorldCover 2021**: Land cover is derived from 2021 Sentinel-2 composites applied to a 2015 historical setting.
5. **No Live Radar or Hydraulic Coupling**: The baseline model does not ingest live Doppler radar, nor does it simulate pipe network routing.
