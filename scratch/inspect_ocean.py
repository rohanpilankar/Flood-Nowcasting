"""
Inspect ocean cells and coastline in grid.
"""
import os
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio

BASE_DIR = r"g:\fl2"
PROCESSED_DIR = os.path.join(BASE_DIR, "Data", "processed")
FINAL_DIR = os.path.join(BASE_DIR, "Data", "final")

grid_p = os.path.join(PROCESSED_DIR, "grids", "chennai_grid_500m.parquet")
gdf = gpd.read_parquet(grid_p)

final_p = os.path.join(FINAL_DIR, "chennai_flood_training.parquet")
df = pd.read_parquet(final_p)

# Look at unique cells from final dataset
cell_df = df[["grid_id", "longitude", "latitude", "water_ratio", "built_up_ratio", "vegetation_ratio", "worldcover_class", "elevation_m", "soil_clay_0_5cm", "building_count", "flood_occurred"]].drop_duplicates("grid_id")

print(f"Total unique cells: {len(cell_df)}")
# Check 100% water or >90% water
ocean_candidates = cell_df[(cell_df["water_ratio"] > 0.90) & (cell_df["built_up_ratio"] == 0) & (cell_df["building_count"] == 0)]
print(f"Candidates with water_ratio > 0.9, built_up=0, bldg_count=0: {len(ocean_candidates)}")

# How many ever flooded?
print(f"Did any of these ocean candidates have flood_occurred=1? {(ocean_candidates['flood_occurred'] == 1).sum()}")

# Check where they are located
print("\nSample ocean candidates:")
print(ocean_candidates[["grid_id", "longitude", "latitude", "water_ratio", "elevation_m", "soil_clay_0_5cm"]].head(20))

# What is the distribution of water_ratio in these?
print("\nWater ratio value counts in >0.9:")
print(ocean_candidates["water_ratio"].value_counts().head(10))

# How many are exactly water_ratio == 1.0?
pure_water = cell_df[cell_df["water_ratio"] == 1.0]
print(f"\nPure water cells (water_ratio == 1.0): {len(pure_water)}")
print(pure_water[["grid_id", "longitude", "latitude", "elevation_m"]].head(15))
