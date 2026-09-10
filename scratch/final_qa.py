"""
Final QA verification of the corrected Chennai flood training dataset.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path("G:/fl2")
FINAL_DIR = BASE_DIR / "Data" / "final"

print("=" * 80)
print("FINAL QA — CORRECTED CHENNAI FLOOD TRAINING DATASET v2.0")
print("=" * 80)

df = pd.read_parquet(FINAL_DIR / "chennai_flood_training.parquet")

PREDICTOR_FEATURES = [
    "rainfall_daily_mm","rainfall_cum_2d_mm","rainfall_cum_3d_mm","rainfall_cum_7d_mm","rainfall_delta_mm",
    "elevation_m","slope_deg","low_lying_score",
    "built_up_ratio","water_ratio","vegetation_ratio","worldcover_class",
    "soil_clay_0_5cm",
    "dist_to_swd_m","dist_to_macro_drain_m","dist_to_micro_drain_m","dist_to_river_stream_m",
    "dist_to_buckingham_canal_m","drainage_density_m_per_km2",
    "building_count","building_area_m2",
    "dist_to_hospital_m","hospital_count_1km","dist_to_fire_station_m","dist_to_police_m",
]

results = {}
all_pass = True

def check(name, condition, actual="", expected=""):
    global all_pass
    status = "PASS" if condition else "FAIL"
    if not condition:
        all_pass = False
    print(f"  [{status}] {name}")
    if actual or expected:
        print(f"         Expected: {expected} | Got: {actual}")
    results[name] = status

print("\n--- STRUCTURE CHECKS ---")
check("Row count >= 50000", len(df) >= 50000, len(df), ">= 50000")
check("Exactly 32 columns", len(df.columns) == 32, len(df.columns), "32")
check("Exactly 25 predictors", len(PREDICTOR_FEATURES) == 25, len(PREDICTOR_FEATURES), "25")
check("No duplicate [grid_id, date]", df.duplicated(subset=["grid_id","date"]).sum() == 0)
check("No NaN values", df.isnull().sum().sum() == 0, df.isnull().sum().sum(), "0")
check("No infinity values", np.isinf(df.select_dtypes(include=np.number)).sum().sum() == 0)
check("Krishna canal NOT present", "dist_to_krishna_water_canal_m" not in df.columns)
check("All 25 predictors present", all(c in df.columns for c in PREDICTOR_FEATURES))

print("\n--- TARGET CHECKS ---")
check("Target values only {0,1}", set(df["flood_occurred"].unique()).issubset({0,1}))
pos = df["flood_occurred"].sum()
neg = (df["flood_occurred"]==0).sum()
check("Positive count > 0", pos > 0, pos, "> 0")
check("Negative count > 0", neg > 0, neg, "> 0")
print(f"         Positives: {pos:,} ({pos/(pos+neg)*100:.2f}%), Negatives: {neg:,}")

print("\n--- COORDINATE CHECKS ---")
check("Latitude in [12.0, 14.0]", (df["latitude"] >= 12.0).all() and (df["latitude"] <= 14.0).all())
check("Longitude in [79.5, 81.0]", (df["longitude"] >= 79.5).all() and (df["longitude"] <= 81.0).all())
unique_cells = df["grid_id"].nunique()
check("Unique grid cells > 1000", unique_cells > 1000, unique_cells, "> 1000")

print("\n--- DATE CHECKS ---")
dates = sorted(df["date"].unique())
check("Date count == 32", len(dates) == 32, len(dates), "32")
check("Min date is 2015-10-01", dates[0] == "2015-10-01")
check("Max date is 2015-12-10", dates[-1] == "2015-12-10")
ACTIVE_FLOOD_DATES = {"2015-11-15","2015-11-16","2015-11-17","2015-11-30","2015-12-01","2015-12-02","2015-12-03","2015-12-04"}
check("All 8 flood event dates present", ACTIVE_FLOOD_DATES.issubset(set(dates)))

print("\n--- TEMPORAL SPLIT CHECKS ---")
train_mask = df["date"] < "2015-11-15"
val_mask = (df["date"] >= "2015-11-15") & (df["date"] <= "2015-11-17")
test_mask = df["date"] >= "2015-11-30"

val_pos = df.loc[val_mask, "flood_occurred"].sum()
test_pos = df.loc[test_mask, "flood_occurred"].sum()
train_pos = df.loc[train_mask, "flood_occurred"].sum()
check("Validation has real positives (>0)", val_pos > 0, val_pos, "> 0")
check("Test has real positives (>0)", test_pos > 0, test_pos, "> 0")
check("Train and val dates don't overlap", set(df.loc[train_mask,"date"].unique()) & set(df.loc[val_mask,"date"].unique()) == set())
check("Val and test dates don't overlap", set(df.loc[val_mask,"date"].unique()) & set(df.loc[test_mask,"date"].unique()) == set())
check("Train < Val < Test (temporal order)", df.loc[train_mask,"date"].max() < df.loc[val_mask,"date"].min())
print(f"         Train: {sorted(df.loc[train_mask,'date'].unique())} -> {train_pos} positives")
print(f"         Val: {sorted(df.loc[val_mask,'date'].unique())} -> {val_pos} positives ({val_pos/val_mask.sum()*100:.1f}%)")
print(f"         Test: {sorted(df.loc[test_mask,'date'].unique())} -> {test_pos} positives ({test_pos/test_mask.sum()*100:.1f}%)")

print("\n--- RAINFALL CHECKS ---")
check("rainfall_daily_mm >= 0", (df["rainfall_daily_mm"] >= 0).all())
check("rainfall_daily_mm <= 500", (df["rainfall_daily_mm"] <= 500).all())
check("cum_2d >= daily always", (df["rainfall_cum_2d_mm"] >= df["rainfall_daily_mm"]).all())
check("cum_3d >= cum_2d always", (df["rainfall_cum_3d_mm"] >= df["rainfall_cum_2d_mm"]).all())
check("cum_7d >= cum_3d always", (df["rainfall_cum_7d_mm"] >= df["rainfall_cum_3d_mm"]).all())

print("\n--- TERRAIN CHECKS ---")
check("elevation_m >= 0", (df["elevation_m"] >= 0).all())
check("slope_deg >= 0", (df["slope_deg"] >= 0).all())
check("low_lying_score in [0,1]", (df["low_lying_score"] >= 0).all() and (df["low_lying_score"] <= 1).all())

print("\n--- LAND COVER CHECKS ---")
check("built_up_ratio in [0,1]", (df["built_up_ratio"] >= 0).all() and (df["built_up_ratio"] <= 1.001).all())
check("water_ratio in [0,1]", (df["water_ratio"] >= 0).all() and (df["water_ratio"] <= 1.001).all())
check("vegetation_ratio in [0,1]", (df["vegetation_ratio"] >= 0).all() and (df["vegetation_ratio"] <= 1.001).all())
valid_classes = {10,20,30,40,50,60,80,90}
check("worldcover_class valid values", set(df["worldcover_class"].unique()).issubset(valid_classes))

print("\n--- SOIL CHECKS ---")
check("soil_clay_0_5cm > 0", (df["soil_clay_0_5cm"] > 0).all())
check("soil_clay_0_5cm <= 1000 g/kg", (df["soil_clay_0_5cm"] <= 1000).all())

print("\n--- DRAINAGE CHECKS ---")
for dc in ["dist_to_swd_m","dist_to_macro_drain_m","dist_to_micro_drain_m","dist_to_river_stream_m","dist_to_buckingham_canal_m"]:
    check(f"{dc} > 0", (df[dc] > 0).all())
check("drainage_density_m_per_km2 >= 0", (df["drainage_density_m_per_km2"] >= 0).all())

print("\n--- LEAKAGE CHECKS ---")
leak_keywords = ["flood","inundation","future","next_day","label","hotspot","historical","target"]
leaked = [c for c in PREDICTOR_FEATURES if any(kw in c.lower() for kw in leak_keywords)]
check("No target-derived or future features", len(leaked) == 0, leaked if leaked else "none", "none")

print("\n--- BUILDING CHECKS ---")
check("building_count >= 0", (df["building_count"] >= 0).all())
check("building_area_m2 >= 0", (df["building_area_m2"] >= 0).all())
has_bldg = df[df["building_count"] > 0]
check("No buildings with zero area", (has_bldg["building_area_m2"] > 0).all())

print("\n--- INFRASTRUCTURE CHECKS ---")
check("dist_to_hospital_m > 0", (df["dist_to_hospital_m"] > 0).all())
check("dist_to_fire_station_m > 0", (df["dist_to_fire_station_m"] > 0).all())
check("dist_to_police_m > 0", (df["dist_to_police_m"] > 0).all())
check("hospital_count_1km >= 0", (df["hospital_count_1km"] >= 0).all())

print("\n--- METADATA CHECKS ---")
with open(FINAL_DIR / "feature_columns.json") as f:
    fc = json.load(f)
check("feature_columns.json total_predictors == 25", fc["total_predictors"] == 25, fc["total_predictors"], "25")
check("Krishna canal not in feature_columns.json", 
      not any(f["feature_name"]=="dist_to_krishna_water_canal_m" for f in fc["features"]))
check("feature_columns.json has 25 feature entries", len(fc["features"]) == 25, len(fc["features"]), "25")

with open(FINAL_DIR / "train_test_splits.json") as f:
    splits = json.load(f)
chrono = splits["chronological_split"]
check("Splits val_positive_count > 0", chrono["val_positive_count"] > 0, chrono["val_positive_count"], "> 0")
check("Splits test_positive_count > 0", chrono["test_positive_count"] > 0, chrono["test_positive_count"], "> 0")
check("Splits val includes 2015-11-15", "2015-11-15" in chrono["val_dates"])
check("Splits test includes 2015-11-30", "2015-11-30" in chrono["test_dates"])

print("\n" + "=" * 80)
if all_pass:
    print("ALL QA CHECKS PASSED")
    print("\n>>> READY_FOR_XGBOOST <<<")
else:
    failed = [k for k,v in results.items() if v == "FAIL"]
    print(f"QA FAILED: {len(failed)} check(s) failed: {failed}")
    print("\n>>> NOT_READY_FOR_XGBOOST <<<")
print("=" * 80)

# Final summary
print(f"\nFINAL DATASET SUMMARY:")
print(f"  Parquet path: G:/fl2/Data/final/chennai_flood_training.parquet")
print(f"  Total rows: {len(df):,}")
print(f"  Unique grid cells: {df['grid_id'].nunique():,}")
print(f"  Unique dates: {df['date'].nunique()}")
print(f"  Predictors: {len(PREDICTOR_FEATURES)}")
print(f"  Target: flood_occurred (0={neg:,}, 1={pos:,}, rate={pos/(pos+neg)*100:.2f}%)")
print(f"  TRAIN: {sorted(df.loc[train_mask,'date'].unique())}")
print(f"  VAL:   {sorted(df.loc[val_mask,'date'].unique())} [{val_pos} positives]")
print(f"  TEST:  {sorted(df.loc[test_mask,'date'].unique())} [{test_pos} positives]")
