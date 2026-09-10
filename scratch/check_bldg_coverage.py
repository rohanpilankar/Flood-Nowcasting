"""
Check building footprints spatial coverage and bounding boxes.
"""
import os
import gzip
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from pyproj import Transformer

BASE_DIR = r"g:\fl2"
RAW_DIR = os.path.join(BASE_DIR, "Data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "Data", "processed")

grid_p = os.path.join(PROCESSED_DIR, "grids", "chennai_grid_500m.parquet")
grid_gdf = gpd.read_parquet(grid_p)
min_x, min_y, max_x, max_y = grid_gdf.total_bounds

bldg_files = [
    "Chennai_Building_Footprints_Microsoft_GML_123312201.csv.gz",
    "Chennai_Building_Footprints_Microsoft_GML_123312203.csv.gz",
    "Chennai_Building_Footprints_Microsoft_GML_123312210.csv.gz",
    "Chennai_Building_Footprints_Microsoft_GML_123312212.csv.gz"
]

transformer_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True)

inside_grid = 0
outside_grid = 0
outside_lats, outside_lons = [], []

for bf in bldg_files:
    with gzip.open(os.path.join(RAW_DIR, bf), "rt", encoding="utf-8") as f:
        for line in f:
            feat = json.loads(line)
            poly = Polygon(feat["geometry"]["coordinates"][0])
            cx, cy = poly.centroid.x, poly.centroid.y
            ux, uy = transformer_to_utm.transform(cx, cy)
            if min_x <= ux <= max_x and min_y <= uy <= max_y:
                inside_grid += 1
            else:
                outside_grid += 1
                if len(outside_lats) < 5:
                    outside_lats.append(cy)
                    outside_lons.append(cx)

print(f"Inside grid bounding box: {inside_grid:,}")
print(f"Outside grid bounding box: {outside_grid:,}")
print(f"Total: {inside_grid + outside_grid:,}")
print(f"Sample outside locations (lat, lon): {list(zip(outside_lats, outside_lons))}")
