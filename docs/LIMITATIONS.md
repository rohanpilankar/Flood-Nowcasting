# System Limitations & Engineering Assumptions — FloodWatch AI

## SIH26085 — Phase 2 Evaluation & Constraints

---

## 1. Provenance & Distinction: Real vs Synthesized Data

To maintain complete academic and engineering integrity in alignment with SIH guidelines:

| Data Layer | Nature in Phase 2 | Real Components | Assumptions & Synthesized Elements |
| :--- | :--- | :--- | :--- |
| **Geographic Extent** | **Real** | Official BMC administrative boundaries, 24 municipal wards, accurate coastlines. | None. Boundary coordinates sourced from MCGM GIS. |
| **Drainage Network** | **Real** | Verified river courses (Mithi River, Poisar, Dahisar, Oshiwara, Mahim Creek). | Minor underground stormwater culvert pipe inner dimensions and silt levels are estimated. |
| **Flood Hotspots** | **Real** | Official BMC 386 benchmark waterlogging spots (Hindmata, Milan Subway, Andheri Subway, Kurla, Sion). | Exact real-time sensor depth readings are simulated based on rainfall and hydraulic accumulation. |
| **Road Network** | **Real** | Major arterial corridors (Western Express Highway, Eastern Express Highway, SV Road, LBS Marg). | Local residential lane graph connectivity is generalized to primary arterial and collector edges. |
| **Topography / Elevation** | **Semi-Real** | SRTM 30m / MCGM elevation profile calibrated to Mumbai saucer basins ($1.5\text{m}$ to $85\text{m}$). | Micro-topography under railway culverts utilizes calibrated depth offsets. |
| **Rainfall Timeseries** | **Calibrated Simulation** | Based on typical Mumbai extreme monsoon storm pulses (e.g., July 26 benchmark convective surges). | Live telemetric IoT rain gauge feeds currently use high-fidelity physics-based storm pulse generators. |

---

## 2. Model Assumptions & Operational Scope

1. **Hydrodynamic vs Machine Learning Trade-off**:
   * Full 2D Saint-Venant hydraulic simulations (e.g., SWMM, HEC-RAS) take hours to run over a $480\text{ km}^2$ metro area.
   * FloodWatch AI replaces slow numerical solvers with a **38.5ms XGBoost surrogate nowcaster** trained on topological terrain depression indices, hydraulic distance to outfalls, and rolling IDW rainfall.
   * **Limitation**: Hydraulic backwater effects from extreme high tides ($>4.5\text{m}$) are parameterized via distance-to-coast and tidal discharge penalties rather than full hydrodynamic tidal wave simulation.

2. **Temporal Horizons**:
   * Validated nowcasting horizons are `NOW`, `+30M`, `+1H`, `+2H`, and `+3H`.
   * Predictions beyond $+3\text{H}$ require Numerical Weather Prediction (NWP) radar assimilation and are outside the scope of convective nowcasting.

3. **Road Routing Engine**:
   * The Dijkstra pathfinder operates on a dynamic directed graph where edge costs reflect both travel length and hazard penalty ($1.0 + (\text{risk}/10)^{2.5}$).
   * Emergency vehicle clearance profiles assume standard SUV / high-clearance emergency response vehicles.

---

## 3. Recommendations for Phase 3 Production Deployment

1. **Hardware Ingestion**: Connect real-time MQTT / LoRaWAN streams from MCGM ultrasonic water level sensors deployed at subways.
2. **Doppler Radar Assimilation**: Ingest direct NetCDF4 reflectivity grids from IMD Santacruz S-band radar.
3. **Citizen Crowdsourcing**: Incorporate geofenced crowd-verified waterlogging reports with automatic anti-spam NLP filters.
