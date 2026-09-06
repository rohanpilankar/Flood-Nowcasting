"""
End-to-End ML Dataset Construction for Mumbai Flood Nowcasting.
Combines dynamic AWS rainfall rolling windows, static GIS terrain/drainage features,
and time-aware ground truth flood labels. Exports Parquet dataset and feature metadata.
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
FINAL_DIR = os.path.join(BASE_DIR, "data", "final")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")


def build_final_ml_dataset():
    print("[*] Loading static spatial features and AWS rainfall...")
    static_df = pd.read_parquet(os.path.join(PROCESSED_DIR, "features", "mumbai_static_spatial_features.parquet"))
    rainfall_raw = pd.read_csv(os.path.join(RAW_DIR, "rainfall", "mumbai_aws_rainfall.csv"))
    rainfall_raw["timestamp"] = pd.to_datetime(rainfall_raw["timestamp"])

    # Unique timestamps and station coordinates
    timestamps = sorted(rainfall_raw["timestamp"].unique())
    stations = rainfall_raw[["station_id", "latitude", "longitude"]].drop_duplicates().set_index("station_id")

    print(f"[*] Total time steps: {len(timestamps)} hours. Processing grid sectors ({len(static_df)})...")

    # For fast IDW weights calculation: compute distance matrix from grid centroids to AWS stations
    grid_coords = static_df[["centroid_lat", "centroid_lon"]].values
    station_coords = stations[["latitude", "longitude"]].values
    station_ids = list(stations.index)

    # Euclidean distance proxy for IDW weights in degrees (squared inverse distance)
    # dist_matrix shape: [num_grids, num_stations]
    diff = grid_coords[:, np.newaxis, :] - station_coords[np.newaxis, :, :]
    dist_sq = np.sum(diff ** 2, axis=-1)
    dist_sq = np.maximum(dist_sq, 1e-6) # avoid div by zero
    weights = 1.0 / dist_sq
    weights = weights / np.sum(weights, axis=1, keepdims=True) # normalize to 1

    # Pivot station rainfall by timestamp: [num_timestamps, num_stations]
    pivoted_rain = rainfall_raw.pivot(index="timestamp", columns="station_id", values="rainfall_mm")[station_ids]

    # Pre-calculate rolling rainfall per station
    rain_1h = pivoted_rain.values
    rain_3h = pivoted_rain.rolling(3, min_periods=1).sum().values
    rain_6h = pivoted_rain.rolling(6, min_periods=1).sum().values
    rain_24h = pivoted_rain.rolling(24, min_periods=1).sum().values

    # Rate of change: delta rainfall 1h
    rain_diff = pivoted_rain.diff().fillna(0.0).values

    # Construct final dataframe across grid sectors and hourly timesteps
    # Subsample timestamps to 72 critical storm monitoring hours for clean dataset size
    step_indices = list(range(12, len(timestamps), 2)) # every 2 hours from hour 12
    selected_timestamps = [timestamps[i] for i in step_indices]

    rows = []
    for t_idx, t_val in enumerate(selected_timestamps):
        orig_t_idx = step_indices[t_idx]
        t_str = t_val.strftime("%Y-%m-%d %H:%M:%S")

        # Interpolate rolling rainfall to grid centroids via IDW
        grid_r1h = np.dot(weights, rain_1h[orig_t_idx, :])
        grid_r3h = np.dot(weights, rain_3h[orig_t_idx, :])
        grid_r6h = np.dot(weights, rain_6h[orig_t_idx, :])
        grid_r24h = np.dot(weights, rain_24h[orig_t_idx, :])
        grid_rdiff = np.dot(weights, rain_diff[orig_t_idx, :])

        # Future rainfall for horizon labels (if within bounds)
        fut_idx_1h = min(orig_t_idx + 1, len(timestamps) - 1)
        fut_idx_2h = min(orig_t_idx + 2, len(timestamps) - 1)
        fut_idx_3h = min(orig_t_idx + 3, len(timestamps) - 1)
        grid_fut_r1h = np.dot(weights, rain_1h[fut_idx_1h, :])
        grid_fut_r3h = np.dot(weights, rain_3h[fut_idx_3h, :])

        for g_idx in range(len(static_df)):
            g_row = static_df.iloc[g_idx]

            r1 = round(float(grid_r1h[g_idx]), 2)
            r3 = round(float(grid_r3h[g_idx]), 2)
            r6 = round(float(grid_r6h[g_idx]), 2)
            r24 = round(float(grid_r24h[g_idx]), 2)
            rdiff = round(float(grid_rdiff[g_idx]), 2)

            elev = g_row["elevation_m"]
            low_lying = g_row["low_lying_score"]
            d_drain = g_row["dist_to_drain_m"]
            hotspot_score = g_row["historical_hotspot_score"]
            built_up = g_row["built_up_ratio"]

            # Hydrological Inundation Target Rule (Ground Truth Label):
            # Flood risk condition: High runoff intensity exceeding localized terrain capacity
            runoff_pressure = (r1 * 0.45 + (r3 / 3.0) * 0.35 + (r24 / 24.0) * 0.20) * built_up
            drainage_attenuation = np.log1p(d_drain) * 0.08 + (elev / 12.0)
            inundation_index = runoff_pressure / max(0.2, drainage_attenuation) + (hotspot_score * 1.8)

            # Binary labels:
            # 1 = Active flood / waterlogging event, 0 = Safe / No flood
            is_flooded_now = 1 if inundation_index >= 3.8 or (r1 >= 38.0 and low_lying >= 0.7) else 0

            # Forward horizons (T+1h, T+2h, T+3h)
            fut_pressure_1h = (float(grid_fut_r1h[g_idx]) * 0.45 + (r3 / 3.0) * 0.35) * built_up
            is_flooded_1h = 1 if (fut_pressure_1h / max(0.2, drainage_attenuation) + hotspot_score * 1.8) >= 3.8 else 0

            fut_pressure_3h = (float(grid_fut_r3h[g_idx]) / 3.0 * 0.8) * built_up
            is_flooded_3h = 1 if (fut_pressure_3h / max(0.2, drainage_attenuation) + hotspot_score * 1.8) >= 3.5 else 0

            rows.append({
                "grid_id": g_row["grid_id"],
                "locality": g_row["locality"],
                "timestamp": t_str,
                "hour_of_day": t_val.hour,
                "centroid_lat": g_row["centroid_lat"],
                "centroid_lon": g_row["centroid_lon"],
                # Dynamic Rainfall
                "rainfall_1h": r1,
                "rainfall_3h": r3,
                "rainfall_6h": r6,
                "rainfall_24h": r24,
                "rainfall_intensity_change": rdiff,
                # Static GIS Features
                "elevation_m": elev,
                "slope_deg": g_row["slope_deg"],
                "low_lying_score": low_lying,
                "dist_to_drain_m": d_drain,
                "drainage_density": g_row["drainage_density"],
                "dist_to_mithi_m": g_row["dist_to_mithi_m"],
                "dist_to_coast_m": g_row["dist_to_coast_m"],
                "historical_hotspot_score": hotspot_score,
                "built_up_ratio": built_up,
                # Inundation Targets
                "flood_event": is_flooded_now,
                "target_plus_1h": is_flooded_1h,
                "target_plus_3h": is_flooded_3h
            })

    final_df = pd.DataFrame(rows)
    print(f"[*] Final ML Dataset shape: {final_df.shape}. Positive class count: {final_df['flood_event'].sum()} ({final_df['flood_event'].mean():.2%})")

    # Save to Parquet and sample CSV
    os.makedirs(FINAL_DIR, exist_ok=True)
    parquet_path = os.path.join(FINAL_DIR, "mumbai_flood_ml_dataset.parquet")
    final_df.to_parquet(parquet_path, index=False)

    sample_csv_path = os.path.join(FINAL_DIR, "mumbai_flood_ml_sample.csv")
    final_df.head(200).to_csv(sample_csv_path, index=False)

    # Save Feature Metadata JSON
    feature_metadata = {
        "dataset_name": "mumbai_flood_ml_dataset",
        "total_samples": len(final_df),
        "total_features": 15,
        "primary_key": ["grid_id", "timestamp"],
        "target_variable": "flood_event",
        "horizon_targets": ["target_plus_1h", "target_plus_3h"],
        "features": [
            {"name": "rainfall_1h", "type": "float", "unit": "mm", "category": "Dynamic Rainfall", "description": "Past 1-hour accumulated precipitation at grid centroid via IDW"},
            {"name": "rainfall_3h", "type": "float", "unit": "mm", "category": "Dynamic Rainfall", "description": "Past 3-hour accumulated precipitation"},
            {"name": "rainfall_6h", "type": "float", "unit": "mm", "category": "Dynamic Rainfall", "description": "Past 6-hour accumulated precipitation"},
            {"name": "rainfall_24h", "type": "float", "unit": "mm", "category": "Dynamic Rainfall", "description": "Past 24-hour antecedent rainfall index"},
            {"name": "rainfall_intensity_change", "type": "float", "unit": "mm/hr", "category": "Dynamic Rainfall", "description": "Acceleration of rainfall rate over preceding hour"},
            {"name": "elevation_m", "type": "float", "unit": "meters", "category": "Static Terrain", "description": "Surface elevation from 30m DEM relative to MSL"},
            {"name": "slope_deg", "type": "float", "unit": "degrees", "category": "Static Terrain", "description": "Topographic surface slope gradient"},
            {"name": "low_lying_score", "type": "float", "unit": "score (0-1)", "category": "Static Terrain", "description": "Topographic depression index indicating water pooling saucer bowl"},
            {"name": "dist_to_drain_m", "type": "float", "unit": "meters", "category": "Static Drainage", "description": "Euclidean metric distance to nearest major stormwater channel / outfall"},
            {"name": "drainage_density", "type": "float", "unit": "km/km2", "category": "Static Drainage", "description": "Channel length density in surrounding catchment"},
            {"name": "dist_to_mithi_m", "type": "float", "unit": "meters", "category": "Static Drainage", "description": "Distance to Mithi River central tidal channel"},
            {"name": "dist_to_coast_m", "type": "float", "unit": "meters", "category": "Static Coastal", "description": "Distance to shoreline (affects tidal backwater drainage gate locks)"},
            {"name": "historical_hotspot_score", "type": "float", "unit": "score (0-1)", "category": "Historical Inundation", "description": "Spatial proximity factor to BMC 386 verified chronic waterlogging locations"},
            {"name": "built_up_ratio", "type": "float", "unit": "ratio (0-1)", "category": "Urban Land Cover", "description": "Impervious surface fraction preventing natural infiltration"},
            {"name": "hour_of_day", "type": "int", "unit": "hour (0-23)", "category": "Temporal", "description": "Diurnal hour of observation"}
        ],
        "class_balance": {
            "negative_samples": int((final_df["flood_event"] == 0).sum()),
            "positive_samples": int((final_df["flood_event"] == 1).sum()),
            "positive_rate": round(float(final_df["flood_event"].mean()), 4)
        },
        "study_area": "Greater Mumbai (BMC)",
        "generated_at": datetime.now().isoformat()
    }

    meta_path = os.path.join(FINAL_DIR, "feature_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(feature_metadata, f, indent=2)

    print(f"[OK] Parquet ML Dataset saved: {parquet_path}")
    print(f"[OK] Feature Metadata saved: {meta_path}")
    return final_df


if __name__ == "__main__":
    build_final_ml_dataset()
