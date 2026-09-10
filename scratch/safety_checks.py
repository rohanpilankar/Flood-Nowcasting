"""
Comprehensive Safety Check Script for Steps 1-4.
"""
import os
import json
import zipfile
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio

BASE_DIR = r"g:\fl2"
RAW_DIR = os.path.join(BASE_DIR, "Data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "Data", "processed")
FINAL_DIR = os.path.join(BASE_DIR, "Data", "final")

def safety_checks():
    print("================================================================")
    print("SAFETY CHECK 1 & 2: DATE INTEGRITY & EVENT WINDOW VALIDATION")
    print("================================================================")
    
    # 1. Inspect final dataset dates
    final_p = os.path.join(FINAL_DIR, "chennai_flood_training.parquet")
    df = pd.read_parquet(final_p)
    dataset_dates = sorted(df["date"].unique())
    print(f"Total unique dates in chennai_flood_training.parquet: {len(dataset_dates)}")
    print(f"Exact dates in dataset:\n{dataset_dates}")
    
    # 2. Inspect raw rainfall dates in 2015
    rain_p = os.path.join(RAW_DIR, "Chennai rainfall.csv")
    df_rain = pd.read_csv(rain_p)
    df_rain["dt"] = pd.to_datetime(df_rain["Date"], format="%d-%m-%Y")
    r2015 = df_rain[(df_rain["dt"] >= "2015-10-01") & (df_rain["dt"] <= "2015-12-15")]
    daily_summary = r2015.groupby("dt")["Rainfall"].agg(["count", "mean", "max"]).reset_index()
    daily_summary["date_str"] = daily_summary["dt"].dt.strftime("%Y-%m-%d")
    
    print("\nRainfall Daily Summary for Oct-Dec 2015 (Significant Rain Days):")
    sig_days = daily_summary[daily_summary["mean"] > 10.0]
    for _, r in sig_days.iterrows():
        print(f"  {r['date_str']}: mean={r['mean']:.1f} mm, max={r['max']:.1f} mm across {r['count']} stations")
        
    # Check ground-truth flood files for date attributes
    clean_zip = os.path.join(RAW_DIR, "FloodWatch_Clean_GeoJSON.zip")
    with zipfile.ZipFile(clean_zip, "r") as z:
        for fn in ["Chennai_Flooding_Points_2015.geojson", "Chennai_Inundation_Depth.geojson"]:
            vpath = f"/vsizip/{clean_zip.replace('\\', '/')}/{fn}"
            gdf = gpd.read_file(vpath)
            print(f"\n{fn} columns: {[c for c in gdf.columns if c != 'geometry']}")
            print(f"{fn} sample properties (first 3):")
            for idx in range(min(3, len(gdf))):
                props = {k: gdf.iloc[idx][k] for k in gdf.columns if k != "geometry"}
                print(f"  [{idx}]: {props}")

    # Check target counts per date in dataset
    print("\nTarget positive count per date in current dataset:")
    date_pos = df.groupby("date")["flood_occurred"].agg(["count", "sum"]).rename(columns={"count": "total_cells", "sum": "positives"})
    date_pos["pos_pct"] = (date_pos["positives"] / date_pos["total_cells"] * 100).round(2)
    print(date_pos[date_pos["positives"] > 0])
    print(f"Dates with 0 positives: {list(date_pos[date_pos['positives'] == 0].index)}")

    print("\n================================================================")
    print("SAFETY CHECK 3: KRISHNA WATER CANAL SPATIAL & HYDROLOGIC AUDIT")
    print("================================================================")
    with zipfile.ZipFile(clean_zip, "r") as z:
        vpath = f"/vsizip/{clean_zip.replace('\\', '/')}/Chennai_Krishna_Water_Canal.geojson"
        kw_gdf = gpd.read_file(vpath)
        print(f"Features: {len(kw_gdf)}")
        print(f"CRS: {kw_gdf.crs}")
        print(f"Total bounds (WGS84): {kw_gdf.total_bounds}")
        for col in kw_gdf.columns:
            if col != "geometry":
                print(f"Attribute {col}: {kw_gdf[col].tolist()}")
                
    grid_p = os.path.join(PROCESSED_DIR, "grids", "chennai_grid_500m.parquet")
    grid_gdf = gpd.read_parquet(grid_p).to_crs("EPSG:4326")
    gb = grid_gdf.total_bounds
    print(f"Chennai Grid Bounds (WGS84): minx={gb[0]:.4f}, miny={gb[1]:.4f}, maxx={gb[2]:.4f}, maxy={gb[3]:.4f}")
    
    # Distance between grid boundary and Krishna Canal
    grid_utm = gpd.read_parquet(grid_p) # in 32644
    kw_utm = kw_gdf.to_crs("EPSG:32644")
    min_dist_to_grid = grid_utm.distance(kw_utm.geometry.iloc[0]).min()
    max_dist_to_grid = grid_utm.distance(kw_utm.geometry.iloc[0]).max()
    print(f"True metric distance from study grid to Krishna Canal:")
    print(f"  Min distance to any grid cell: {min_dist_to_grid/1000.0:.2f} km")
    print(f"  Max distance to any grid cell: {max_dist_to_grid/1000.0:.2f} km")

    print("\n================================================================")
    print("SAFETY CHECK 4: OCEAN MASK VS WETLANDS / MARSHES / ESTUARIES")
    print("================================================================")
    # Examine the water cells
    cell_df = df[["grid_id", "longitude", "latitude", "water_ratio", "built_up_ratio", "vegetation_ratio", "elevation_m"]].drop_duplicates("grid_id")
    
    # Let's inspect candidate ocean cells vs known wetlands
    # Known wetland regions:
    # Pallikaranai: lat 12.92 to 12.97, lon 80.20 to 80.23
    # Ennore Creek: lat 13.20 to 13.26, lon 80.30 to 80.34
    # Adyar Estuary: lat 13.00 to 13.02, lon 80.26 to 80.28
    # Muttukadu / Kovalam Creek: lat 12.83 to 12.87, lon 80.23 to 80.25
    
    cand_ocean = cell_df[(cell_df["water_ratio"] > 0.95) & (cell_df["built_up_ratio"] == 0.0) & (cell_df["elevation_m"] <= 1.0)]
    print(f"Total candidate cells (water > 0.95, built_up == 0, elev <= 1m): {len(cand_ocean)}")
    
    # Break down by longitude
    print(f"Candidates with lon < 80.25 (Inland / Western): {len(cand_ocean[cand_ocean['longitude'] < 80.25])}")
    if len(cand_ocean[cand_ocean['longitude'] < 80.25]) > 0:
        print(cand_ocean[cand_ocean['longitude'] < 80.25])
        
    print(f"Candidates with lon >= 80.25: {len(cand_ocean[cand_ocean['longitude'] >= 80.25])}")
    
    # Check if any candidate cell falls inside Pallikaranai
    palli = cand_ocean[(cand_ocean["latitude"] >= 12.92) & (cand_ocean["latitude"] <= 12.97) & (cand_ocean["longitude"] >= 80.20) & (cand_ocean["longitude"] <= 80.24)]
    print(f"Candidates inside Pallikaranai box: {len(palli)}")
    
    # Check all candidate cells with lon >= 80.25 to see their exact coordinates
    c8025 = cand_ocean[cand_ocean["longitude"] >= 80.25]
    print(f"Min lon: {c8025['longitude'].min()}, Max lon: {c8025['longitude'].max()}")
    print(f"Min lat: {c8025['latitude'].min()}, Max lat: {c8025['latitude'].max()}")

if __name__ == "__main__":
    safety_checks()
