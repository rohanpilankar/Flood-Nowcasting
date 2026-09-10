"""
Inspect why candidates had building counts.
"""
import os
import pandas as pd

BASE_DIR = r"g:\fl2"
FINAL_DIR = os.path.join(BASE_DIR, "Data", "final")
df = pd.read_parquet(os.path.join(FINAL_DIR, "chennai_flood_training.parquet"))
cell_df = df[["grid_id", "longitude", "latitude", "water_ratio", "built_up_ratio", "elevation_m", "building_count", "building_area_m2"]].drop_duplicates("grid_id")

cand = cell_df[(cell_df["water_ratio"] > 0.95) & (cell_df["built_up_ratio"] == 0.0) & (cell_df["elevation_m"] <= 1.0) & (cell_df["longitude"] >= 80.25)]

with_bldg = cand[cand["building_count"] > 0]
print(f"Candidates with building_count > 0: {len(with_bldg)}")
if len(with_bldg) > 0:
    print(with_bldg.head(20))
else:
    print("Zero candidates have building_count > 0!")
    print(f"Direct sum: {cand['building_count'].sum()}")
