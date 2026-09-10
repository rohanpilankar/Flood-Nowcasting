"""
Classify water cells into inland lakes vs Bay of Bengal ocean cells.
"""
import os
import pandas as pd
import geopandas as gpd

BASE_DIR = r"g:\fl2"
PROCESSED_DIR = os.path.join(BASE_DIR, "Data", "processed")
FINAL_DIR = os.path.join(BASE_DIR, "Data", "final")

df = pd.read_parquet(os.path.join(FINAL_DIR, "chennai_flood_training.parquet"))
cell_df = df[["grid_id", "longitude", "latitude", "water_ratio", "built_up_ratio", "vegetation_ratio", "worldcover_class", "elevation_m", "soil_clay_0_5cm", "building_count"]].drop_duplicates("grid_id")

water_cells = cell_df[cell_df["water_ratio"] >= 0.8]
print(f"Total cells with water_ratio >= 0.8: {len(water_cells)}")

# Look at their coordinates:
# Coastal ocean cells will be on the eastern edge (Bay of Bengal)
# Puzhal lake is around 80.18-80.22, 13.15-13.20, elev > 10m
# Chembarambakkam / Porur are west (80.1-80.15)
inland = water_cells[water_cells["longitude"] < 80.25]
coastal_ocean = water_cells[water_cells["longitude"] >= 80.25]

print(f"Inland water cells (lon < 80.25): {len(inland)}")
print(f"Sample inland:\n{inland[['grid_id', 'longitude', 'latitude', 'elevation_m', 'water_ratio']].head(10)}")

print(f"\nCoastal / Ocean water cells (lon >= 80.25): {len(coastal_ocean)}")
print(f"Sample coastal/ocean:\n{coastal_ocean[['grid_id', 'longitude', 'latitude', 'elevation_m', 'water_ratio']].head(20)}")

# Check how many are elevation == 0 and water_ratio == 1.0 along the coast:
ocean_bay = coastal_ocean[(coastal_ocean["elevation_m"] <= 1.0) & (coastal_ocean["water_ratio"] > 0.95)]
print(f"\nClear Bay of Bengal ocean cells (lon >= 80.25, elev <= 1.0, water_ratio > 0.95): {len(ocean_bay)}")
print(ocean_bay[['grid_id', 'longitude', 'latitude', 'elevation_m', 'water_ratio']].describe())
