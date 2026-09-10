import pandas as pd, json, numpy as np
from pathlib import Path

FINAL = Path("G:/fl2/Data/final")
df = pd.read_parquet(FINAL / "chennai_flood_training.parquet")

print("=== CURRENT STATE ===")
print(f"Shape: {df.shape}")
print(f"Columns ({len(df.columns)}): {list(df.columns)}")
print(f"Unique cells: {df['grid_id'].nunique()}")
print(f"Unique dates: {df['date'].nunique()}")
print(f"All dates: {sorted(df['date'].unique())}")
print(f"Duplicates [grid_id,date]: {df.duplicated(['grid_id','date']).sum()}")
print(f"NaN total: {df.isnull().sum().sum()}")
print(f"Inf total: {np.isinf(df.select_dtypes(include=np.number)).sum().sum()}")
print(f"\nflood_occurred distribution:")
print(df["flood_occurred"].value_counts())
print(f"Positive rate: {df['flood_occurred'].mean()*100:.2f}%")

with open(FINAL / "train_test_splits.json") as f:
    splits = json.load(f)
ch = splits["chronological_split"]
print("\n=== CURRENT SPLITS ===")
print(f"TRAIN dates: {ch['train_dates']}")
print(f"TRAIN positives: {ch['train_positive_count']}")
print(f"VAL dates: {ch['val_dates']}")
print(f"VAL positives: {ch['val_positive_count']}")
print(f"TEST dates: {ch['test_dates']}")
print(f"TEST positives: {ch['test_positive_count']}")

FLOOD_DATES = ["2015-11-15","2015-11-16","2015-11-17",
               "2015-11-30","2015-12-01","2015-12-02","2015-12-03","2015-12-04"]
print("\n=== POSITIVES PER FLOOD DATE ===")
for d in FLOOD_DATES:
    rows = (df["date"]==d).sum()
    pos  = df[df["date"]==d]["flood_occurred"].sum()
    print(f"  {d}: {rows} rows, {pos} positives")

print("\n=== FEATURE RANGES (static per cell) ===")
PREDICTORS = [c for c in df.columns if c not in
    ["grid_id","date","latitude","longitude","x_utm","y_utm","flood_occurred"]]
print(f"Predictors ({len(PREDICTORS)}): {PREDICTORS}")
print(f"\n{'Feature':<35} {'dtype':>8} {'min':>10} {'max':>10} {'mean':>10} {'median':>10} {'std':>10} {'miss':>6} {'uniq':>6}")
print("-"*115)
for col in PREDICTORS:
    s = df[col]
    print(f"{col:<35} {str(s.dtype):>8} {s.min():>10.3f} {s.max():>10.3f} {s.mean():>10.3f} {s.median():>10.3f} {s.std():>10.3f} {s.isna().sum():>6} {s.nunique():>6}")
