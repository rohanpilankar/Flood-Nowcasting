"""
Inspect all drainage layers and Krishna Water Canal in detail.
"""
import os
import zipfile
import geopandas as gpd
import pandas as pd

BASE_DIR = r"g:\fl2"
RAW_DIR = os.path.join(BASE_DIR, "Data", "raw")
clean_zip = os.path.join(RAW_DIR, "FloodWatch_Clean_GeoJSON.zip")

drain_layers = [
    "Chennai_Storm_Water_Drains_2023.geojson",
    "Chennai_Basin_Macro_Drains.geojson",
    "Chennai_Basin_Micro_Drains.geojson",
    "Chennai_Basin_Rivers_Streams.geojson",
    "Chennai_Buckingham_Canal.geojson",
    "Chennai_Krishna_Water_Canal.geojson"
]

with zipfile.ZipFile(clean_zip, "r") as z:
    for dn in drain_layers:
        vpath = f"/vsizip/{clean_zip.replace('\\', '/')}/{dn}"
        gdf = gpd.read_file(vpath)
        print(f"\n=== {dn} ===")
        print(f"Features: {len(gdf)}")
        print(f"CRS: {gdf.crs}")
        print(f"Bounds (WGS84): {gdf.total_bounds}")
        gdf_utm = gdf.to_crs("EPSG:32644")
        tot_len_km = gdf_utm.geometry.length.sum() / 1000.0
        print(f"Total length: {tot_len_km:.2f} km")
        print(f"Columns: {[c for c in gdf.columns if c != 'geometry']}")
        if len(gdf) <= 5:
            for idx, row in gdf.iterrows():
                props = {k: row[k] for k in gdf.columns if k != "geometry"}
                print(f"  Feature {idx}: {props}")

# Check study area grid bounds
grid_p = os.path.join(BASE_DIR, "Data", "processed", "grids", "chennai_grid_500m.parquet")
grid_gdf = gpd.read_parquet(grid_p).to_crs("EPSG:4326")
print(f"\nChennai Study Grid Bounds: {grid_gdf.total_bounds}")
