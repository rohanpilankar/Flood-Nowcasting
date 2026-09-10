"""
Check Krishna canal correlations with spatial coordinates and other predictors.
"""
import os
import pandas as pd

BASE_DIR = r"g:\fl2"
df = pd.read_parquet(os.path.join(BASE_DIR, "Data", "final", "chennai_flood_training.parquet"))

sub = df[["x_utm", "y_utm", "dist_to_krishna_water_canal_m", "dist_to_buckingham_canal_m", "dist_to_river_stream_m", "flood_occurred"]].drop_duplicates()
print("Correlations:")
print(sub.corr()["dist_to_krishna_water_canal_m"])
