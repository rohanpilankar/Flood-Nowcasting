# Drainage Network & Hydraulic Telemetry Interface Specification

## Scientific Status
```text
STATUS: FUTURE DATA INTERFACE
CURRENT DRAINAGE TELEMETRY: NOT AVAILABLE
```

> [!WARNING]
> This document defines a prospective data and graph schema for dynamic drainage network telemetry and 1D/2D hydraulic coupling.
> **Dynamic drainage telemetry, live manhole sensors, pipe cross-sections, and calibrated hydraulic solvers are NOT present in the current repository.**
> The current project does **NOT** execute EPA-SWMM, 1D Saint-Venant hydrodynamic equations, 2D shallow water solvers (e.g., LISFLOOD-FP, HEC-RAS 2D), or coupled 1D-2D pipe-surface simulations. The baseline model is an empirical statistical susceptibility model across a static 500m grid.

---

## 1. Interface Overview

This schema provides the architectural data contract required to interface a physical urban drainage network (manholes, outfalls, culverts, underground storm drains, open canals) with hydrodynamic simulation engines and machine learning surrogates.

---

## 2. Static Network Topology Schema

### A. Nodes Schema (`nodes`)
Defines junction manholes, inlets, storage retention ponds, and coastal/river outfalls.

| Field Name | Type | Units | Nullable | Description / Physical Semantics |
| :--- | :--- | :--- | :---: | :--- |
| `node_id` | String | Identifier | NO | Unique alphanumeric node identifier (e.g., `MH_TNAGAR_0412`). |
| `node_type` | String | Categorical | NO | Node typology (`junction`, `inlet`, `outfall`, `retention_pond`). |
| `latitude` | Float | Decimal Degrees | NO | WGS84 Geographic Latitude. |
| `longitude` | Float | Decimal Degrees | NO | WGS84 Geographic Longitude. |
| `rim_elevation_m` | Float | Meters (MSL) | NO | Ground surface / street rim elevation above Mean Sea Level. |
| `invert_elevation_m` | Float | Meters (MSL) | NO | Node invert elevation (bottom of manhole chamber) above MSL. |
| `storage_capacity_m3` | Float | Cubic meters ($m^3$) | YES | Chamber surcharge / retention storage capacity. |

### B. Edges Schema (`edges`)
Defines conduits, subterranean closed conduits, stormwater pipes, box drains, and open masonry canals.

| Field Name | Type | Units | Nullable | Description / Physical Semantics |
| :--- | :--- | :--- | :---: | :--- |
| `edge_id` | String | Identifier | NO | Unique conduit identifier (e.g., `CND_SWD_8841`). |
| `from_node` | String | Identifier | NO | Inlet / upstream junction `node_id`. |
| `to_node` | String | Identifier | NO | Outlet / downstream junction `node_id`. |
| `length_m` | Float | Meters | NO | Conduit segment physical length. |
| `diameter_m` | Float | Meters | YES | Internal circular diameter (for circular pipes). |
| `width_m` | Float | Meters | YES | Conduit internal base width (for rectangular box drains/canals). |
| `height_m` | Float | Meters | YES | Conduit internal maximum height (for rectangular box drains/canals). |
| `slope` | Float | Dimensionless (m/m)| NO | Hydraulic gradient ($S_0 = \Delta z / L$). |
| `mannings_n` | Float | $s / m^{1/3}$ | NO | Boundary roughness coefficient (Manning's $n$). |
| `capacity_m3_s` | Float | $m^3/s$ | NO | Maximum gravity conveyance capacity under free surface flow. |

---

## 3. Dynamic State Telemetry Schema (`dynamic_state`)

Captures real-time sensor observations and hydrodynamic numerical state variables at discrete timestamps.

| Field Name | Type | Units | Nullable | Description / Physical Semantics |
| :--- | :--- | :--- | :---: | :--- |
| `timestamp` | ISO 8601 Timestamp | `YYYY-MM-DDTHH:MM:SSZ` | NO | Telemetry or simulation state epoch. |
| `inflow_m3_s` | Float | $m^3/s$ | NO | Total lateral catchment stormwater discharge entering node. |
| `water_level_m` | Float | Meters (MSL) | NO | Absolute stage / hydraulic head inside node or edge. |
| `surcharge` | Boolean / Int | Binary (0/1) | NO | 1 if water head exceeds pipe crown / manhole rim (pressurized flow). |
| `blockage_factor` | Float | Ratio $[0.0, 1.0]$ | NO | Solid waste / siltation constriction coefficient (0: clear, 1: blocked). |
| `backflow_velocity_m_s` | Float | $m/s$ | YES | Tidal or high-stage downstream reverse velocity ($v < 0$). |

---

## 4. Hydraulic Simulation Boundary Disclosures

1. **Absence of Live Telemetry**: No automated ultrasonic level sensors, SCADA outfall monitoring, or sewer CCTV inspection feeds currently exist in the repository.
2. **Absence of Dynamic Solvers**: The project currently uses static proximity metrics (`dist_to_swd_m`, `dist_to_macro_drain_m`, etc.) and does not solve dynamic Navier-Stokes or Saint-Venant mass/momentum equations.
3. **Prohibition of Fabricated Network Parameters**: Conduits, diameters, slopes, and manhole rims must be obtained from real municipal engineering surveys (GCC/CMWSSB) before deployment.
