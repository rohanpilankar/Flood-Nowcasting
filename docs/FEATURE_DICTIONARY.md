# Feature Dictionary — Mumbai Urban Flood Nowcasting

| Feature Name | Category | Type | Unit | Formula / Source | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `rainfall_1h` | Dynamic Rainfall | Float | mm | $R_t - R_{t-1h}$ (IDW) | Accumulated rainfall over past 1 hour |
| `rainfall_3h` | Dynamic Rainfall | Float | mm | $\sum_{k=0}^2 R_{t-k}$ | Accumulated rainfall over past 3 hours |
| `rainfall_6h` | Dynamic Rainfall | Float | mm | $\sum_{k=0}^5 R_{t-k}$ | Intermediate storm volume index |
| `rainfall_24h` | Dynamic Rainfall | Float | mm | $\sum_{k=0}^{23} R_{t-k}$ | Antecedent soil moisture saturation index |
| `rainfall_intensity_change` | Dynamic Rainfall | Float | mm/hr | $R_{1h}(t) - R_{1h}(t-1h)$ | Precipitation acceleration/deceleration |
| `elevation_m` | Static Topography | Float | meters | Copernicus DEM 30m | Elevation relative to Mean Sea Level (MSL) |
| `slope_deg` | Static Topography | Float | degrees | $\arctan(\sqrt{dz/dx^2 + dz/dy^2})$ | Topographic terrain incline angle |
| `low_lying_score` | Static Topography | Float | 0.0 - 1.0 | Normalized inverted elevation | Identifies concave saucer basins & underpasses |
| `dist_to_drain_m` | Static Drainage | Float | meters | Euclidean in EPSG:32643 | Metric distance to nearest major storm drain |
| `drainage_density` | Static Drainage | Float | km/km² | Line length / area | Density of stormwater channels in catchment |
| `dist_to_mithi_m` | Static Drainage | Float | meters | Distance to Mithi vector | Proximity to Mithi River tidal corridor |
| `dist_to_coast_m` | Static Coastal | Float | meters | Distance to coastline | Marine outfall tidal backpressure sensitivity |
| `historical_hotspot_score` | Historical Inundation | Float | 0.0 - 1.0 | $\exp(-d_{\text{hotspot}} / 1200)$ | Kernel density decay score to BMC 386 hotspots |
| `built_up_ratio` | Urban Land Cover | Float | 0.0 - 1.0 | Impervious fraction | Paved concrete and asphalt impervious fraction |
| `hour_of_day` | Temporal | Integer | 0 - 23 | $t.\text{hour}$ | Diurnal municipal drainage maintenance cycle |
