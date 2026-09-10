"""
Inspect SoilGrids nodata cells: breakdown by land cover, urban, water, and ocean.
"""
import os
import numpy as np
import pandas as pd
import rasterio

BASE_DIR = r"g:\fl2"
PROCESSED_DIR = os.path.join(BASE_DIR, "Data", "processed")

soil_utm = os.path.join(PROCESSED_DIR, "rasters", "chennai_soil_clay_250m_utm44n.tif")
static_p = os.path.join(PROCESSED_DIR, "features", "chennai_static_spatial_features.parquet")
sdf = pd.read_parquet(static_p)

with rasterio.open(soil_utm) as src:
    sample_pts = [(r.x_utm, r.y_utm) for _, r in sdf.iterrows()]
    sampled = [v[0] for v in src.sample(sample_pts)]
    sdf["raw_soil"] = sampled

sdf["is_soil_nodata"] = (sdf["raw_soil"] == -1) | (sdf["raw_soil"] <= 0)

print(f"Total cells: {len(sdf)}")
print(f"Native valid soil cells: {(~sdf['is_soil_nodata']).sum()} ({(~sdf['is_soil_nodata']).mean()*100:.1f}%)")
print(f"Soil nodata cells: {sdf['is_soil_nodata'].sum()} ({sdf['is_soil_nodata'].mean()*100:.1f}%)")

nodata_df = sdf[sdf["is_soil_nodata"]]
print("\nLand cover breakdown of soil nodata cells:")
print(f"Mean built_up_ratio: {nodata_df['built_up_ratio'].mean():.3f}")
print(f"Mean water_ratio: {nodata_df['water_ratio'].mean():.3f}")
print(f"Mean vegetation_ratio: {nodata_df['vegetation_ratio'].mean():.3f}")

# How many nodata are water / ocean?
ocean_nodata = nodata_df[(nodata_df["water_ratio"] > 0.95) & (nodata_df["elevation_m"] <= 1.0) & (nodata_df["longitude"] >= 80.25)]
print(f"Soil nodata that are pure Bay of Bengal ocean: {len(ocean_nodata)}")

# How many nodata are inland water (lakes/reservoirs)?
inland_water_nodata = nodata_df[(nodata_df["water_ratio"] > 0.8) & (nodata_df["longitude"] < 80.25)]
print(f"Soil nodata that are inland lakes/waterbodies: {len(inland_water_nodata)}")

# How many nodata are terrestrial urban built-up?
urban_nodata = nodata_df[(nodata_df["built_up_ratio"] > 0.3)]
print(f"Soil nodata that are urban built-up (built_up > 0.3): {len(urban_nodata)}")

# Check what SoilGrids 2.0 does:
# In SoilGrids 2.0 (ISRIC), urban land (sealed surfaces) and open water surfaces are systematically masked out.
print("\nNative valid soil land cover breakdown:")
valid_df = sdf[~sdf["is_soil_nodata"]]
print(f"Mean built_up_ratio: {valid_df['built_up_ratio'].mean():.3f}")
print(f"Mean water_ratio: {valid_df['water_ratio'].mean():.3f}")
print(f"Mean vegetation_ratio: {valid_df['vegetation_ratio'].mean():.3f}")
