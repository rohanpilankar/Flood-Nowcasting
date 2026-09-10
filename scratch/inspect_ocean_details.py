"""
Detailed spatial inspection of candidate ocean cells vs coastline and estuaries.
"""
import os
import pandas as pd
import geopandas as gpd
import rasterio

BASE_DIR = r"g:\fl2"
PROCESSED_DIR = os.path.join(BASE_DIR, "Data", "processed")
FINAL_DIR = os.path.join(BASE_DIR, "Data", "final")

df = pd.read_parquet(os.path.join(FINAL_DIR, "chennai_flood_training.parquet"))
cell_df = df[["grid_id", "longitude", "latitude", "x_utm", "y_utm", "water_ratio", "built_up_ratio", "vegetation_ratio", "elevation_m", "building_count"]].drop_duplicates("grid_id")

# Filter candidates
cand = cell_df[(cell_df["water_ratio"] > 0.95) & (cell_df["built_up_ratio"] == 0.0) & (cell_df["elevation_m"] <= 1.0) & (cell_df["longitude"] >= 80.25)]

print(f"Total candidate cells: {len(cand)}")
print(f"Water ratio breakdown in candidates:")
print(cand["water_ratio"].value_counts())

# Check how many are 100% water (water_ratio == 1.000)
pure_water = cand[cand["water_ratio"] == 1.000]
print(f"\n100% pure water cells: {len(pure_water)}")

# What about the non-100% water cells?
non_pure = cand[cand["water_ratio"] < 1.000]
print(f"\nCells with 0.95 < water_ratio < 1.0: {len(non_pure)}")
print(non_pure[["grid_id", "longitude", "latitude", "water_ratio", "vegetation_ratio", "elevation_m"]])

# Check if any building footprint exists in candidates
print(f"\nTotal buildings in candidates: {cand['building_count'].sum()}")

# Check if any candidate cell has ever flooded in the ground truth
gt_flooded = df[(df["grid_id"].isin(cand["grid_id"])) & (df["flood_occurred"] == 1)]
print(f"Total flood observations in candidates: {len(gt_flooded)}")

# Check distance from the shoreline for the non-pure cells
# Let's inspect their coordinates:
for idx, r in non_pure.iterrows():
    print(f"  {r['grid_id']}: lon={r['longitude']:.6f}, lat={r['latitude']:.6f}, water={r['water_ratio']:.3f}, veg={r['vegetation_ratio']:.3f}, elev={r['elevation_m']:.2f}")
