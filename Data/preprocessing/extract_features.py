"""
Step 4: Comprehensive Feature Extraction for Chennai Urban Flood Nowcasting.
Extracts static environmental features (Terrain, Soil, Land Cover, Drainage,
Buildings, Critical Infrastructure) and dynamic meteorological features
(IDW Daily Rainfall, Antecedent Rolling Sums, Delta Intensity).
"""

import os
import gzip
import json
import logging
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from shapely.geometry import Point, Polygon
from pyproj import Transformer
import rasterio
from rasterio.windows import from_bounds
from scipy.ndimage import uniform_filter
from scipy.interpolate import NearestNDInterpolator

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("ExtractFeatures")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_DIR = os.path.join(BASE_DIR, "Data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "Data", "processed")
GRIDS_DIR = os.path.join(PROCESSED_DIR, "grids")
RASTERS_DIR = os.path.join(PROCESSED_DIR, "rasters")
VECTORS_DIR = os.path.join(PROCESSED_DIR, "vectors")
FEATURES_DIR = os.path.join(PROCESSED_DIR, "features")

TARGET_CRS = "EPSG:32644"

# Authoritative geocoding mapping for all 62 rain gauge stations in Chennai rainfall.csv
STATION_COORDINATES_WGS84 = {
    "Chennai port trust": (80.2975, 13.0844),
    "Sholinganallur": (80.2279, 12.9010),
    "Chennai nungambakkam": (80.2425, 13.0627),
    "Alandur": (80.2025, 13.0048),
    "MYLAPORE-TRIPLICANE TALUK": (80.2642, 13.0488),
    "Ambathur": (80.1548, 13.1143),
    "Gov hr sec school MGR Nagar": (80.1989, 13.0336),
    "Ayanavaram taluk office": (80.2324, 13.0970),
    "Perambur Corporation park": (80.2435, 13.1095),
    "DGP Office": (80.2796, 13.0440),
    "Anna university": (80.2354, 13.0102),
    "Chennai collectorate building": (80.2882, 13.0888),
    "Chennai AP": (80.1709, 12.9941),
    "Pachaiyappa college": (80.2335, 13.0784),
    "Govt. arts college": (80.2396, 13.0298),
    "Purasawalkam - Perambur": (80.2558, 13.0885),
    "CD Hospital Tondiarpet": (80.2872, 13.1258),
    "Zone 01 Kathivakkam": (80.3160, 13.2040),
    "Zone 01 Thiruvottiyur": (80.3012, 13.1610),
    "Zone 02 Manali": (80.2625, 13.1706),
    "Zone 02 D15 Manali": (80.2625, 13.1706),
    "Zone 03 Madhavaram": (80.2314, 13.1489),
    "Zone 03 Puzhal": (80.2016, 13.1554),
    "Zone 04 Tondiarpet": (80.2872, 13.1258),
    "Zone 05 Royapuram": (80.2941, 13.1118),
    "Zone 05 GCC": (80.2785, 13.0825),
    "Zone 06 D65 Kolathur": (80.2180, 13.1250),
    "Zone 06 T.V.K Nagar": (80.2328, 13.1190),
    "Zone 07 Ambattur": (80.1548, 13.1143),
    "Zone 07 U18 D81 Vanagaram": (80.1550, 13.0610),
    "Zone 08 Anna Nagar": (80.2100, 13.0850),
    "Zone 08 Malar colony": (80.2030, 13.0810),
    "Zone 09 Teynampet": (80.2500, 13.0410),
    "Zone 09 Ice House": (80.2740, 13.0530),
    "Zone 10 Kodambakkam": (80.2200, 13.0515),
    "Zone 11 U32 Maduravoyal": (80.1680, 13.0640),
    "Zone 11 Valasaravakkam": (80.1747, 13.0410),
    "Zone 12 Alandhur": (80.2025, 13.0048),
    "Zone 12 Meenambakkam": (80.1790, 12.9850),
    "Zone 12 D156 Mugalivakkam": (80.1690, 13.0180),
    "Zone 13 Adyar": (80.2565, 13.0012),
    "Zone 13 U39 Adyar": (80.2520, 13.0040),
    "Zone 13 Adyar Eco Park": (80.2680, 13.0190),
    "Zone 14 Perungudi": (80.2461, 12.9654),
    "Zone 14 U41 Perungudi": (80.2420, 12.9610),
    "Zone 15 Sholinganallur": (80.2279, 12.9010),
    "Zone 15 Uthandi": (80.2480, 12.8620),
    "Ezhilgam": (80.2828, 13.0645),
    "Ambattur": (80.1548, 13.1143),
    "Puzhal": (80.2016, 13.1554),
    "Royapuram": (80.2941, 13.1118),
    "Tondairpet": (80.2872, 13.1258),
    "Thiru-Vi-Ka Nagar": (80.2328, 13.1190),
    "Anna Nagar": (80.2100, 13.0850),
    "Thiruvottiyur": (80.3012, 13.1610),
    "Adyar": (80.2565, 13.0012),
    "Perungudi": (80.2461, 12.9654),
    "Teynampet": (80.2500, 13.0410),
    "Valasaravakkam": (80.1747, 13.0410),
    "Kodambakkam": (80.2200, 13.0515),
    "Manali": (80.2625, 13.1706),
    "Madhavaram": (80.2314, 13.1489)
}


def extract_static_features(grid_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    logger.info("Extracting static terrain, soil, land cover, drainage, building, and infrastructure features...")
    os.makedirs(FEATURES_DIR, exist_ok=True)
    df = grid_gdf[["grid_id", "x_utm", "y_utm", "longitude", "latitude"]].copy()

    cell_pts = [Point(x, y) for x, y in zip(df["x_utm"], df["y_utm"])]
    cell_boxes = grid_gdf.geometry.values

    # -------------------------------------------------------------
    # 1. DEM & Terrain Derivatives
    # -------------------------------------------------------------
    dem_path = os.path.join(RASTERS_DIR, "chennai_dem_30m_utm44n.tif")
    if os.path.exists(dem_path):
        logger.info("Extracting elevation and terrain slope...")
        with rasterio.open(dem_path) as src:
            dem_arr = src.read(1)
            nodata = src.nodata

            # Compute slope in degrees
            res_x, res_y = src.res
            dy, dx = np.gradient(dem_arr, res_y, res_x)
            slope_deg_arr = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))

            # Neighborhood elevation for saucer depression index (approx 3km window = 101 pixels)
            valid_mask = (dem_arr != nodata) & (dem_arr > -100)
            clean_dem = np.where(valid_mask, dem_arr, 0.0)
            neighborhood_elev = uniform_filter(clean_dem, size=101, mode="nearest")
            depression_arr = neighborhood_elev - clean_dem # positive if lower than surroundings

            coords = [(r.x_utm, r.y_utm) for _, r in df.iterrows()]
            sampled_elev = [v[0] for v in src.sample(coords)]
            df["elevation_m"] = [round(max(0.0, float(e)), 2) for e in sampled_elev]

            # Sample slope
            rows, cols = rasterio.transform.rowcol(src.transform, df["x_utm"].values, df["y_utm"].values)
            rows = np.clip(rows, 0, slope_deg_arr.shape[0] - 1)
            cols = np.clip(cols, 0, slope_deg_arr.shape[1] - 1)
            df["slope_deg"] = [round(float(s), 2) for s in slope_deg_arr[rows, cols]]

            # Low-lying depression score (normalized 0 to 1)
            raw_dep = depression_arr[rows, cols]
            min_d, max_d = np.percentile(raw_dep, 1), np.percentile(raw_dep, 99)
            norm_dep = np.clip((raw_dep - min_d) / max(1e-3, (max_d - min_d)), 0.0, 1.0)
            df["low_lying_score"] = [round(float(d), 3) for d in norm_dep]

    # -------------------------------------------------------------
    # 2. SoilGrids Clay Content (0-5 cm)
    # -------------------------------------------------------------
    soil_path = os.path.join(RASTERS_DIR, "chennai_soil_clay_250m_utm44n.tif")
    if os.path.exists(soil_path):
        logger.info("Extracting SoilGrids clay content (g/kg)...")
        with rasterio.open(soil_path) as src:
            coords = [(r.x_utm, r.y_utm) for _, r in df.iterrows()]
            sampled_soil = [v[0] for v in src.sample(coords)]
            soil_vals = np.array([float(s) if s != src.nodata and s > 0 else np.nan for s in sampled_soil])
            
            # Scientific spatial interpolation for urban sealed core:
            # SoilGrids 2.0 explicitly masks impermeable built-up surfaces as 0/nodata.
            # We preserve the underlying geological continuity of native alluvial soils by interpolating
            # from valid natural terrestrial soil samples using nearest-neighbor geospatial interpolation.
            valid_mask = ~np.isnan(soil_vals)
            if np.sum(valid_mask) > 0:
                train_coords = np.array(coords)[valid_mask]
                train_vals = soil_vals[valid_mask]
                interp = NearestNDInterpolator(train_coords, train_vals)
                interpolated_vals = interp(coords)
                df["soil_clay_0_5cm"] = [round(float(v), 1) for v in interpolated_vals]
                logger.info(f"SoilGrids: {np.sum(valid_mask)} native soil cells, {np.sum(~valid_mask)} urban sealed cells interpolated via geological continuity.")
            else:
                df["soil_clay_0_5cm"] = 200.0

    # -------------------------------------------------------------
    # 3. ESA WorldCover 2021 (10m)
    # -------------------------------------------------------------
    wc_path = os.path.join(RASTERS_DIR, "chennai_worldcover_10m_utm44n.tif")
    if os.path.exists(wc_path):
        logger.info("Extracting WorldCover land use ratios and majority class...")
        with rasterio.open(wc_path) as src:
            built_ratios, water_ratios, veg_ratios, majority_classes = [], [], [], []
            for geom in cell_boxes:
                win = from_bounds(*geom.bounds, src.transform)
                arr = src.read(1, window=win)
                valid = arr[arr != src.nodata]
                if len(valid) > 0:
                    b_ratio = np.mean(valid == 50) # Built-up
                    w_ratio = np.mean(valid == 80) # Water
                    v_ratio = np.mean(np.isin(valid, [10, 20, 30, 40])) # Tree, shrub, grass, crop
                    vals, counts = np.unique(valid, return_counts=True)
                    mode_cls = vals[np.argmax(counts)]
                else:
                    b_ratio, w_ratio, v_ratio, mode_cls = 0.5, 0.0, 0.5, 50
                built_ratios.append(round(float(b_ratio), 3))
                water_ratios.append(round(float(w_ratio), 3))
                veg_ratios.append(round(float(v_ratio), 3))
                majority_classes.append(int(mode_cls))

            df["built_up_ratio"] = built_ratios
            df["water_ratio"] = water_ratios
            df["vegetation_ratio"] = veg_ratios
            df["worldcover_class"] = majority_classes

    # -------------------------------------------------------------
    # 4. Drainage Network Distance Fields & Density
    # -------------------------------------------------------------
    drain_layers = [
        ("Chennai_Storm_Water_Drains_2023.parquet", "dist_to_swd_m"),
        ("Chennai_Basin_Macro_Drains.parquet", "dist_to_macro_drain_m"),
        ("Chennai_Basin_Micro_Drains.parquet", "dist_to_micro_drain_m"),
        ("Chennai_Basin_Rivers_Streams.parquet", "dist_to_river_stream_m"),
        ("Chennai_Buckingham_Canal.parquet", "dist_to_buckingham_canal_m"),
        ("Chennai_Krishna_Water_Canal.parquet", "dist_to_krishna_water_canal_m")
    ]

    for fname, colname in drain_layers:
        p = os.path.join(VECTORS_DIR, fname)
        if os.path.exists(p):
            logger.info(f"Computing metric distance to {colname}...")
            gdf_drain = gpd.read_parquet(p)
            lines = gdf_drain.geometry.values
            tree = shapely.STRtree(lines)
            _, dists = tree.query_nearest(cell_pts, return_distance=True, all_matches=False)
            df[colname] = [round(float(d), 1) for d in dists]

    # Local drainage density: length of SWD per km2 within each 500m cell (area = 0.25 km2)
    swd_p = os.path.join(VECTORS_DIR, "Chennai_Storm_Water_Drains_2023.parquet")
    if os.path.exists(swd_p):
        logger.info("Computing local drainage density (m / km2)...")
        gdf_swd = gpd.read_parquet(swd_p)
        swd_tree = shapely.STRtree(gdf_swd.geometry.values)
        densities = []
        for geom in cell_boxes:
            candidate_idxs = swd_tree.query(geom, predicate="intersects")
            if len(candidate_idxs) > 0:
                total_len = sum(gdf_swd.geometry.iloc[idx].intersection(geom).length for idx in candidate_idxs)
                density = total_len / 0.25 # m / km2
            else:
                density = 0.0
            densities.append(round(float(density), 1))
        df["drainage_density_m_per_km2"] = densities

    # -------------------------------------------------------------
    # 5. Microsoft Building Footprints
    # -------------------------------------------------------------
    logger.info("Aggregating Microsoft building footprints (869,486 footprints)...")
    transformer_to_utm = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)

    bldg_files = [
        "Chennai_Building_Footprints_Microsoft_GML_123312201.csv.gz",
        "Chennai_Building_Footprints_Microsoft_GML_123312203.csv.gz",
        "Chennai_Building_Footprints_Microsoft_GML_123312210.csv.gz",
        "Chennai_Building_Footprints_Microsoft_GML_123312212.csv.gz"
    ]

    # Grid spatial index for O(1) point binning
    min_x, min_y, max_x, max_y = grid_gdf.total_bounds
    res = 500.0
    cols_n = int(np.ceil((max_x - min_x) / res))
    rows_n = int(np.ceil((max_y - min_y) / res))

    cell_lookup = {}
    for idx, r in df.iterrows():
        c = int((r.x_utm - min_x) // res)
        rw = int((r.y_utm - min_y) // res)
        cell_lookup[(c, rw)] = idx

    bldg_counts = np.zeros(len(df), dtype=int)
    bldg_areas = np.zeros(len(df), dtype=float)

    for bf in bldg_files:
        bf_path = os.path.join(RAW_DIR, bf)
        if os.path.exists(bf_path):
            with gzip.open(bf_path, "rt", encoding="utf-8") as f:
                for line in f:
                    try:
                        feat = json.loads(line)
                        coords = feat["geometry"]["coordinates"][0]
                        # Compute centroid roughly
                        poly = Polygon(coords)
                        cx, cy = poly.centroid.x, poly.centroid.y
                        utm_x, utm_y = transformer_to_utm.transform(cx, cy)
                        c = int((utm_x - min_x) // res)
                        rw = int((utm_y - min_y) // res)
                        if (c, rw) in cell_lookup:
                            target_idx = cell_lookup[(c, rw)]
                            bldg_counts[target_idx] += 1
                            # Approx area in m2: 1 deg lat ~ 111,000m, 1 deg lon ~ 108,000m
                            bldg_areas[target_idx] += poly.area * (111000 * 108000)
                    except Exception:
                        continue

    df["building_count"] = bldg_counts
    df["building_area_m2"] = [round(float(a), 1) for a in bldg_areas]

    # -------------------------------------------------------------
    # 6. Critical Infrastructure
    # -------------------------------------------------------------
    crit_p = os.path.join(VECTORS_DIR, "chennai_critical_infrastructure.parquet")
    if os.path.exists(crit_p):
        logger.info("Extracting critical infrastructure proximity and counts...")
        gdf_crit = gpd.read_parquet(crit_p)

        # Hospitals & clinics
        hospitals = gdf_crit[gdf_crit["amenity"].isin(["hospital", "clinic"])].copy()
        if len(hospitals) > 0:
            h_tree = shapely.STRtree(hospitals.geometry.values)
            _, h_dists = h_tree.query_nearest(cell_pts, return_distance=True, all_matches=False)
            df["dist_to_hospital_m"] = [round(float(d), 1) for d in h_dists]
            # Count within 1 km
            h_counts_1km = [len(h_tree.query(geom.buffer(1000.0), predicate="intersects")) for geom in cell_pts]
            df["hospital_count_1km"] = h_counts_1km
        else:
            df["dist_to_hospital_m"] = 5000.0
            df["hospital_count_1km"] = 0

        # Police
        police = gdf_crit[gdf_crit["amenity"] == "police"].copy()
        if len(police) > 0:
            p_tree = shapely.STRtree(police.geometry.values)
            _, p_dists = p_tree.query_nearest(cell_pts, return_distance=True, all_matches=False)
            df["dist_to_police_m"] = [round(float(d), 1) for d in p_dists]
        else:
            df["dist_to_police_m"] = 5000.0

        # Fire stations
        fire = gdf_crit[gdf_crit["amenity"] == "fire_station"].copy()
        if len(fire) > 0:
            f_tree = shapely.STRtree(fire.geometry.values)
            _, f_dists = f_tree.query_nearest(cell_pts, return_distance=True, all_matches=False)
            df["dist_to_fire_station_m"] = [round(float(d), 1) for d in f_dists]
        else:
            df["dist_to_fire_station_m"] = 10000.0

    out_parquet = os.path.join(FEATURES_DIR, "chennai_static_spatial_features.parquet")
    out_csv = os.path.join(FEATURES_DIR, "chennai_static_spatial_features.csv")
    df.to_parquet(out_parquet)
    df.to_csv(out_csv, index=False)
    logger.info(f"Saved static features: {out_parquet} ({len(df)} rows, {len(df.columns)} columns)")
    return df


def interpolate_rainfall_timeseries(grid_df: pd.DataFrame, dates: list = None) -> pd.DataFrame:
    """
    Interpolates daily rainfall telemetry to grid cells using Inverse Distance Weighting (IDW).
    Computes rolling antecedent totals (2d, 3d, 7d) and 1-day delta intensity.
    """
    logger.info("Computing dynamic rainfall interpolation (IDW) and rolling antecedent totals...")
    rain_path = os.path.join(RAW_DIR, "Chennai rainfall.csv")
    df_rain = pd.read_csv(rain_path)
    df_rain["parsed_date"] = pd.to_datetime(df_rain["Date"], format="%d-%m-%Y")

    # Map station coordinates
    transformer_to_utm = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)
    station_lut = {}
    for st_name, (lon, lat) in STATION_COORDINATES_WGS84.items():
        x_utm, y_utm = transformer_to_utm.transform(lon, lat)
        station_lut[st_name] = (x_utm, y_utm)

    # Filter to stations present in coordinates LUT
    df_rain = df_rain[df_rain["Station"].isin(station_lut)].copy()
    df_rain["x_utm"] = df_rain["Station"].map(lambda s: station_lut[s][0])
    df_rain["y_utm"] = df_rain["Station"].map(lambda s: station_lut[s][1])

    # If specific dates not requested, select the 2015 flood disaster sequence and representative monsoon dates
    if dates is None:
        # 2015 Chennai Deluge sequence: 2015-11-10 to 2015-12-10 (31 days)
        # Plus representative dry/moderate monsoon baseline days from 2015 to evaluate non-flood performance
        dates = pd.date_range("2015-11-10", "2015-12-10").tolist()
        # Add dry and moderate rain days from 2015
        extra_dates = [
            pd.Timestamp("2015-10-01"), pd.Timestamp("2015-10-15"), pd.Timestamp("2015-10-25"),
            pd.Timestamp("2015-10-28"), pd.Timestamp("2015-10-30"), pd.Timestamp("2015-11-02"),
            pd.Timestamp("2015-11-05"), pd.Timestamp("2015-11-08")
        ]
        dates = sorted(list(set(dates + extra_dates)))

    grid_coords = grid_df[["x_utm", "y_utm"]].values # [num_cells, 2]
    timeseries_rows = []

    # Sort all rainfall dates for rolling calculation
    all_dates = sorted(df_rain["parsed_date"].unique())
    date_to_idx = {d: i for i, d in enumerate(all_dates)}

    # Pivot station rainfall: index=parsed_date, columns=Station
    pivoted = df_rain.pivot_table(index="parsed_date", columns="Station", values="Rainfall", aggfunc="mean").fillna(0.0)

    for target_date in dates:
        if target_date not in pivoted.index:
            continue

        target_date_ts = pd.Timestamp(target_date)
        date_str = target_date_ts.strftime("%Y-%m-%d")

        # Active reporting stations on this date
        day_records = df_rain[df_rain["parsed_date"] == target_date_ts]
        if len(day_records) == 0:
            continue

        st_names = day_records["Station"].unique()
        st_coords = np.array([station_lut[s] for s in st_names]) # [num_active_st, 2]
        st_rain = np.array([day_records[day_records["Station"] == s]["Rainfall"].values[0] for s in st_names])

        # IDW distance matrix (metric meters)
        diff = grid_coords[:, np.newaxis, :] - st_coords[np.newaxis, :, :] # [num_cells, num_active_st, 2]
        dist_sq = np.sum(diff**2, axis=-1) # [num_cells, num_active_st]
        dist_sq = np.maximum(dist_sq, 100.0**2) # minimum 100m distance threshold to prevent singularity
        weights = 1.0 / dist_sq
        weights /= np.sum(weights, axis=1, keepdims=True)

        grid_rain_daily = np.dot(weights, st_rain)

        # Antecedent rolling sums (2-day, 3-day, 7-day) strictly looking backward in time
        # Get past dates up to target_date
        curr_idx = date_to_idx.get(target_date_ts, 0)
        
        # 2-day sum (current + previous day)
        p2_dates = [all_dates[i] for i in range(max(0, curr_idx - 1), curr_idx + 1)]
        p2_st_sum = pivoted.loc[p2_dates, st_names].sum(axis=0).values
        grid_rain_2d = np.dot(weights, p2_st_sum)

        # 3-day sum
        p3_dates = [all_dates[i] for i in range(max(0, curr_idx - 2), curr_idx + 1)]
        p3_st_sum = pivoted.loc[p3_dates, st_names].sum(axis=0).values
        grid_rain_3d = np.dot(weights, p3_st_sum)

        # 7-day sum (soil saturation index)
        p7_dates = [all_dates[i] for i in range(max(0, curr_idx - 6), curr_idx + 1)]
        p7_st_sum = pivoted.loc[p7_dates, st_names].sum(axis=0).values
        grid_rain_7d = np.dot(weights, p7_st_sum)

        # 1-day delta: rain_t - rain_{t-1}
        if curr_idx > 0:
            prev_date = all_dates[curr_idx - 1]
            prev_st_rain = pivoted.loc[prev_date, st_names].values
            grid_rain_prev = np.dot(weights, prev_st_rain)
            grid_delta = grid_rain_daily - grid_rain_prev
        else:
            grid_delta = np.zeros_like(grid_rain_daily)

        for g_idx, grid_id in enumerate(grid_df["grid_id"]):
            timeseries_rows.append({
                "grid_id": grid_id,
                "date": date_str,
                "rainfall_daily_mm": round(float(grid_rain_daily[g_idx]), 2),
                "rainfall_cum_2d_mm": round(float(grid_rain_2d[g_idx]), 2),
                "rainfall_cum_3d_mm": round(float(grid_rain_3d[g_idx]), 2),
                "rainfall_cum_7d_mm": round(float(grid_rain_7d[g_idx]), 2),
                "rainfall_delta_mm": round(float(grid_delta[g_idx]), 2)
            })

    rain_df = pd.DataFrame(timeseries_rows)
    logger.info(f"Generated dynamic rainfall records: {len(rain_df)} rows across {len(dates)} dates.")
    return rain_df
