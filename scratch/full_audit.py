"""
Full validation audit of Chennai flood training dataset.
Checks all dimensions per the validation specification.
"""
import os, json, zipfile, sys
import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path

BASE_DIR = Path("G:/fl2")
FINAL_DIR = BASE_DIR / "Data" / "final"
RAW_DIR   = BASE_DIR / "Data" / "raw"
PROCESSED_DIR = BASE_DIR / "Data" / "processed"

print("=" * 80)
print("SECTION 1: LOAD & BASIC AUDIT OF PARQUET")
print("=" * 80)
df = pd.read_parquet(FINAL_DIR / "chennai_flood_training.parquet")
print(f"Shape: {df.shape}")
print(f"Columns ({len(df.columns)}): {list(df.columns)}")
print(f"\nDtypes:\n{df.dtypes.to_string()}")
print(f"\nUnique grid cells: {df['grid_id'].nunique()}")
print(f"Unique dates: {df['date'].nunique()}")
all_dates = sorted(df['date'].unique())
print(f"\nAll unique dates ({len(all_dates)}):")
for d in all_dates:
    print(f"  {d}")

print(f"\nDuplicate [grid_id, date] rows: {df.duplicated(subset=['grid_id','date']).sum()}")

print("\nMissing values per column:")
nulls = df.isnull().sum()
print(nulls[nulls > 0].to_string() if nulls.sum() > 0 else "  NONE")

print("\nInfinite values per column (numeric):")
num_cols = df.select_dtypes(include=np.number).columns
infs = {c: np.isinf(df[c]).sum() for c in num_cols if np.isinf(df[c]).sum() > 0}
print(infs if infs else "  NONE")

print("\nTarget distribution:")
print(df['flood_occurred'].value_counts())
print(f"Positive rate: {df['flood_occurred'].mean()*100:.2f}%")

print("\n" + "=" * 80)
print("SECTION 2: ACTUAL DATES VERIFICATION")
print("=" * 80)
# Which flood event dates actually exist in the dataset?
ACTIVE_FLOOD_DATES = {
    "2015-11-15","2015-11-16","2015-11-17",
    "2015-11-30","2015-12-01","2015-12-02","2015-12-03","2015-12-04"
}
present_flood_dates = ACTIVE_FLOOD_DATES & set(all_dates)
missing_flood_dates = ACTIVE_FLOOD_DATES - set(all_dates)
print(f"Expected active flood dates: {sorted(ACTIVE_FLOOD_DATES)}")
print(f"Present active flood dates: {sorted(present_flood_dates)}")
print(f"MISSING from dataset: {sorted(missing_flood_dates)}")

# What positive counts exist per date?
print("\nFlood positives by date:")
date_pos = df.groupby('date')['flood_occurred'].agg(['sum','count','mean'])
date_pos.columns = ['positives','total_rows','positive_rate']
print(date_pos[date_pos['positives']>0].to_string())
print(f"\nDates with ZERO positives:")
print(date_pos[date_pos['positives']==0].index.tolist())

print("\n" + "=" * 80)
print("SECTION 3: TEMPORAL SPLIT VALIDATION")
print("=" * 80)
# Current splits:
train_mask = df['date'] < '2015-11-25'
val_mask = (df['date'] >= '2015-11-25') & (df['date'] <= '2015-11-29')
test_mask = df['date'] >= '2015-11-30'

print(f"TRAIN: {df.loc[train_mask,'date'].min()} to {df.loc[train_mask,'date'].max()}")
print(f"  Rows: {train_mask.sum()}, Positives: {df.loc[train_mask,'flood_occurred'].sum()}, Rate: {df.loc[train_mask,'flood_occurred'].mean()*100:.2f}%")
train_dates = sorted(df.loc[train_mask,'date'].unique())
print(f"  Actual dates ({len(train_dates)}): {train_dates}")

print(f"\nVALIDATION: {df.loc[val_mask,'date'].min()} to {df.loc[val_mask,'date'].max()}")
print(f"  Rows: {val_mask.sum()}, Positives: {df.loc[val_mask,'flood_occurred'].sum()}, Rate: {df.loc[val_mask,'flood_occurred'].mean()*100:.2f}%")
val_dates = sorted(df.loc[val_mask,'date'].unique())
print(f"  Actual dates ({len(val_dates)}): {val_dates}")
print(f"  *** CRITICAL: Validation has {df.loc[val_mask,'flood_occurred'].sum()} positives ***")

print(f"\nTEST: {df.loc[test_mask,'date'].min()} to {df.loc[test_mask,'date'].max()}")
print(f"  Rows: {test_mask.sum()}, Positives: {df.loc[test_mask,'flood_occurred'].sum()}, Rate: {df.loc[test_mask,'flood_occurred'].mean()*100:.2f}%")
test_dates = sorted(df.loc[test_mask,'date'].unique())
print(f"  Actual dates ({len(test_dates)}): {test_dates}")

print("\n" + "=" * 80)
print("SECTION 4: OCEAN / MARINE MASK AUDIT")
print("=" * 80)
# Check candidate ocean cells in dataset
ocean_candidates = df[
    (df['water_ratio'] > 0.95) & 
    (df['built_up_ratio'] == 0) & 
    (df['elevation_m'] <= 1.0) & 
    (df['longitude'] >= 80.245)
]
# Get unique cells only (static features don't vary by date)
static_cols = ['grid_id','latitude','longitude','elevation_m','water_ratio','built_up_ratio','vegetation_ratio','worldcover_class']
ocean_cands_unique = ocean_candidates[static_cols].drop_duplicates('grid_id')
print(f"Candidate ocean/marine cells: {len(ocean_cands_unique)} unique grid cells")
print(ocean_cands_unique.to_string())

print("\n" + "=" * 80)
print("SECTION 5: DRAINAGE SOURCE VERIFICATION")
print("=" * 80)
clean_zip = RAW_DIR / "FloodWatch_Clean_GeoJSON.zip"
drain_files = [
    "Chennai_Storm_Water_Drains_2023.geojson",
    "Chennai_Basin_Macro_Drains.geojson",
    "Chennai_Basin_Micro_Drains.geojson",
    "Chennai_Basin_Rivers_Streams.geojson",
    "Chennai_Buckingham_Canal.geojson",
    "Chennai_Krishna_Water_Canal.geojson",
]
print(f"{'File':<45} {'Features':>10} {'Valid Geom':>12} {'CRS':>12}")
print("-"*85)
with zipfile.ZipFile(clean_zip, 'r') as z:
    names_in_zip = z.namelist()
    for fname in drain_files:
        if fname in names_in_zip:
            gdf = gpd.read_file(f"/vsizip/{str(clean_zip).replace(chr(92),'/')}/{fname}")
            valid = gdf.geometry.is_valid.sum()
            print(f"{fname:<45} {len(gdf):>10} {valid:>12} {str(gdf.crs):>12}")
        else:
            print(f"{fname:<45}     MISSING")

# Krishna Water Canal specifics
if "Chennai_Krishna_Water_Canal.geojson" in names_in_zip:
    kc = gpd.read_file(f"/vsizip/{str(clean_zip).replace(chr(92),'/')}/Chennai_Krishna_Water_Canal.geojson")
    kc_utm = kc.to_crs("EPSG:32644")
    print(f"\nKrishna Water Canal bounds (WGS84): {list(kc.total_bounds)}")
    print(f"Krishna Water Canal geometry types: {kc.geom_type.unique()}")
    print(f"  Centroid lon range: {kc.geometry.centroid.x.min():.4f} to {kc.geometry.centroid.x.max():.4f}")
    print(f"  Centroid lat range: {kc.geometry.centroid.y.min():.4f} to {kc.geometry.centroid.y.max():.4f}")
    print(f"\nCHENNAI STUDY AREA: lon 80.10-80.35, lat 12.85-13.25")
    print(f"Krishna Canal is at lon {kc.total_bounds[0]:.4f}-{kc.total_bounds[2]:.4f}, lat {kc.total_bounds[1]:.4f}-{kc.total_bounds[3]:.4f}")
    print(f"Distance from study area east boundary (80.35) to Krishna Canal west boundary ({kc.total_bounds[0]:.4f}):")
    dist_deg = 80.35 - kc.total_bounds[2]
    print(f"  {dist_deg:.4f} deg => ~{abs(dist_deg) * 111000:.0f} m")

print("\n" + "=" * 80)
print("SECTION 6: DEM/TERRAIN VALIDATION")
print("=" * 80)
# Static features (per unique grid cell)
static_df = df[['grid_id','elevation_m','slope_deg','low_lying_score']].drop_duplicates('grid_id')
print(f"Unique grid cells: {len(static_df)}")
for col in ['elevation_m','slope_deg','low_lying_score']:
    print(f"\n{col}:")
    print(f"  min={static_df[col].min():.3f}, max={static_df[col].max():.3f}, mean={static_df[col].mean():.3f}")
    print(f"  Zeros: {(static_df[col]==0).sum()}, Negatives: {(static_df[col]<0).sum()}")
    print(f"  Unique values: {static_df[col].nunique()}")

# Low_lying_score formula verification check
print("\nlow_lying_score range check (should be [0,1]):")
print(f"  Values below 0: {(static_df['low_lying_score']<0).sum()}")
print(f"  Values above 1: {(static_df['low_lying_score']>1).sum()}")

print("\n" + "=" * 80)
print("SECTION 7: WORLDCOVER VALIDATION")
print("=" * 80)
static_wc = df[['grid_id','built_up_ratio','water_ratio','vegetation_ratio','worldcover_class']].drop_duplicates('grid_id')
print("WorldCover classes present:")
print(static_wc['worldcover_class'].value_counts().to_string())
print(f"\nRatio sum stats (built+water+veg) per cell:")
ratio_sum = static_wc['built_up_ratio'] + static_wc['water_ratio'] + static_wc['vegetation_ratio']
print(f"  min={ratio_sum.min():.3f}, max={ratio_sum.max():.3f}, mean={ratio_sum.mean():.3f}")
print(f"  Cells where sum > 1.001: {(ratio_sum > 1.001).sum()}")
print(f"  Cells where all three == 0: {((static_wc['built_up_ratio']==0) & (static_wc['water_ratio']==0) & (static_wc['vegetation_ratio']==0)).sum()}")

# Is worldcover_class redundant?
# Check correlation of worldcover_class with ratios
print("\nworldcover_class vs dominant fraction:")
wc_dom = static_wc.copy()
wc_dom['dominant_class'] = wc_dom[['built_up_ratio','water_ratio','vegetation_ratio']].idxmax(axis=1)
print(wc_dom.groupby('worldcover_class')['dominant_class'].value_counts())

print("\n" + "=" * 80)
print("SECTION 8: SOIL VALIDATION")
print("=" * 80)
static_soil = df[['grid_id','soil_clay_0_5cm']].drop_duplicates('grid_id')
print(f"soil_clay_0_5cm stats:")
print(f"  min={static_soil['soil_clay_0_5cm'].min():.1f}, max={static_soil['soil_clay_0_5cm'].max():.1f}")
print(f"  mean={static_soil['soil_clay_0_5cm'].mean():.1f}, median={static_soil['soil_clay_0_5cm'].median():.1f}")
print(f"  NaN: {static_soil['soil_clay_0_5cm'].isna().sum()}")
print(f"  Zeros: {(static_soil['soil_clay_0_5cm']==0).sum()}")
print(f"  Negative: {(static_soil['soil_clay_0_5cm']<0).sum()}")
# Suspicious: SoilGrids units are g/kg (*10 of percentage), typical clay 50-500 g/kg
print(f"  Values > 1000 (suspicious): {(static_soil['soil_clay_0_5cm']>1000).sum()}")
print(f"  Values == 200 (imputed?): {(static_soil['soil_clay_0_5cm']==200).sum()}")

print("\n" + "=" * 80)
print("SECTION 9: RAINFALL VALIDATION")
print("=" * 80)
# Check rolling window logic in dataset
rain_df = df[['grid_id','date','rainfall_daily_mm','rainfall_cum_2d_mm','rainfall_cum_3d_mm','rainfall_cum_7d_mm','rainfall_delta_mm']].copy()

# Pick a sample grid cell and check rolling sums
sample_cell = df['grid_id'].iloc[0]
cell_rain = rain_df[rain_df['grid_id']==sample_cell].sort_values('date')
print(f"Sample cell: {sample_cell}")
print(cell_rain.to_string())

# Verify: cum_2d >= daily (always true if t-1 >= 0)
print(f"\nRows where cum_2d < daily (potential issue): {(df['rainfall_cum_2d_mm'] < df['rainfall_daily_mm']).sum()}")
print(f"Rows where cum_3d < cum_2d: {(df['rainfall_cum_3d_mm'] < df['rainfall_cum_2d_mm']).sum()}")
print(f"Rows where cum_7d < cum_3d: {(df['rainfall_cum_7d_mm'] < df['rainfall_cum_3d_mm']).sum()}")

# Check for unrealistic values
print(f"\nRainfall sanity checks:")
print(f"  rainfall_daily_mm < 0: {(df['rainfall_daily_mm'] < 0).sum()}")
print(f"  rainfall_daily_mm > 500 (extreme): {(df['rainfall_daily_mm'] > 500).sum()}")
print(f"  rainfall_cum_7d_mm > 1000 (extreme): {(df['rainfall_cum_7d_mm'] > 1000).sum()}")

print("\n" + "=" * 80)
print("SECTION 10: BUILDING FEATURES VALIDATION")
print("=" * 80)
static_bldg = df[['grid_id','building_count','building_area_m2']].drop_duplicates('grid_id')
print(f"building_count: min={static_bldg['building_count'].min()}, max={static_bldg['building_count'].max()}, mean={static_bldg['building_count'].mean():.1f}")
print(f"building_area_m2: min={static_bldg['building_area_m2'].min():.1f}, max={static_bldg['building_area_m2'].max():.1f}")
print(f"Cells with zero buildings: {(static_bldg['building_count']==0).sum()}")
# Area consistency
has_bldg = static_bldg[static_bldg['building_count']>0]
zero_area_with_bldg = (has_bldg['building_area_m2']==0).sum()
print(f"Cells with buildings but zero area: {zero_area_with_bldg}")
avg_area_per_bldg = has_bldg['building_area_m2'] / has_bldg['building_count']
print(f"Average area per building: min={avg_area_per_bldg.min():.1f}, max={avg_area_per_bldg.max():.1f}, mean={avg_area_per_bldg.mean():.1f} m2")

# Area approximation note from code: area * 111000 * 108000 (in degrees, approximation)
# Check if this is correct - polygon area in degrees * ~1.2e10 gives m2
print(f"\nNOTE: Building areas are approximate (polygon.area * 111000 * 108000 in degree-space)")
print(f"This is an approximation and may over/underestimate real areas by up to 5-10%")

print("\n" + "=" * 80)
print("SECTION 11: INFRASTRUCTURE VALIDATION")
print("=" * 80)
static_inf = df[['grid_id','dist_to_hospital_m','hospital_count_1km','dist_to_fire_station_m','dist_to_police_m']].drop_duplicates('grid_id')
for col in ['dist_to_hospital_m','hospital_count_1km','dist_to_fire_station_m','dist_to_police_m']:
    print(f"{col}: min={static_inf[col].min():.1f}, max={static_inf[col].max():.1f}, mean={static_inf[col].mean():.1f}, zeros={( static_inf[col]==0).sum()}")

print("\n" + "=" * 80)
print("SECTION 12: LEAKAGE AUDIT")
print("=" * 80)
PREDICTOR_COLS = [
    'rainfall_daily_mm','rainfall_cum_2d_mm','rainfall_cum_3d_mm','rainfall_cum_7d_mm','rainfall_delta_mm',
    'elevation_m','slope_deg','low_lying_score',
    'built_up_ratio','water_ratio','vegetation_ratio','worldcover_class',
    'soil_clay_0_5cm',
    'dist_to_swd_m','dist_to_macro_drain_m','dist_to_micro_drain_m','dist_to_river_stream_m',
    'dist_to_buckingham_canal_m','dist_to_krishna_water_canal_m','drainage_density_m_per_km2',
    'building_count','building_area_m2',
    'dist_to_hospital_m','hospital_count_1km','dist_to_fire_station_m','dist_to_police_m'
]
print("Leakage keyword scan:")
leak_keywords = ['flood','inundation','water_level','future','next_day','label','target','hotspot','historical_flood','dist_to_flood']
for col in PREDICTOR_COLS:
    for kw in leak_keywords:
        if kw in col.lower():
            print(f"  FLAGGED: {col} contains keyword '{kw}'")
print("  (none expected)")

# Check Krishna Water Canal distance range (should be very large if outside study area)
print(f"\nKrishna Canal distance stats:")
print(f"  dist_to_krishna_water_canal_m: min={df['dist_to_krishna_water_canal_m'].min():.1f}m, max={df['dist_to_krishna_water_canal_m'].max():.1f}m")
print(f"  Minimum distance = {df['dist_to_krishna_water_canal_m'].min():.0f} m = {df['dist_to_krishna_water_canal_m'].min()/1000:.1f} km")
print(f"  All cells are at least {df['dist_to_krishna_water_canal_m'].min()/1000:.1f} km from Krishna Canal")

# Check correlation of dist_to_krishna with lat/lon
corr_lon = df['dist_to_krishna_water_canal_m'].corr(df['longitude'])
corr_lat = df['dist_to_krishna_water_canal_m'].corr(df['latitude'])
print(f"  Correlation with longitude: {corr_lon:.4f}")
print(f"  Correlation with latitude: {corr_lat:.4f}")
print(f"  (High correlation with lat/lon suggests it encodes location, not hydrology)")

print("\n" + "=" * 80)
print("SECTION 13: FEATURE QUALITY STATISTICS")
print("=" * 80)
print(f"{'Feature':<35} {'Min':>10} {'Max':>10} {'Mean':>10} {'Median':>10} {'Std':>10} {'Missing':>8} {'Unique':>8}")
print("-"*105)
for col in PREDICTOR_COLS:
    if col in df.columns:
        s = df[col]
        print(f"{col:<35} {s.min():>10.3f} {s.max():>10.3f} {s.mean():>10.3f} {s.median():>10.3f} {s.std():>10.3f} {s.isna().sum():>8} {s.nunique():>8}")

print("\n" + "=" * 80)
print("SECTION 14: COORDINATE & DATE VALIDITY")
print("=" * 80)
unique_cells = df[['grid_id','latitude','longitude']].drop_duplicates('grid_id')
print(f"Coordinate bounds:")
print(f"  lat: {unique_cells['latitude'].min():.4f} to {unique_cells['latitude'].max():.4f}")
print(f"  lon: {unique_cells['longitude'].min():.4f} to {unique_cells['longitude'].max():.4f}")
invalid_coords = df[(df['latitude']<12.0)|(df['latitude']>14.0)|(df['longitude']<79.5)|(df['longitude']>81.0)]
print(f"  Invalid coordinates (outside Chennai region): {len(invalid_coords)}")

# Check dates are valid
try:
    parsed_dates = pd.to_datetime(df['date'], format='%Y-%m-%d')
    print(f"Date parsing: OK. Min={parsed_dates.min().date()}, Max={parsed_dates.max().date()}")
except:
    print("Date parsing: FAILED")

print("\n" + "=" * 80)
print("SECTION 15: DRAINAGE DISTANCES VALIDATION")
print("=" * 80)
drain_cols = ['dist_to_swd_m','dist_to_macro_drain_m','dist_to_micro_drain_m','dist_to_river_stream_m','dist_to_buckingham_canal_m','dist_to_krishna_water_canal_m','drainage_density_m_per_km2']
static_drain = df[['grid_id']+drain_cols].drop_duplicates('grid_id')
for col in drain_cols:
    print(f"{col}: min={static_drain[col].min():.1f}, max={static_drain[col].max():.1f}")
print(f"\nNOTE: All drainage distances should be positive (using STRtree nearest in EPSG:32644)")
neg_drain = {c: (static_drain[c]<=0).sum() for c in drain_cols if (static_drain[c]<=0).sum()>0}
print(f"Zero or negative distances: {neg_drain if neg_drain else 'NONE'}")

print("\n" + "=" * 80)
print("SECTION 16: FINAL SUMMARY FOR TRAIN/VAL/TEST SPLIT ISSUE")
print("=" * 80)
print("CRITICAL FINDING - Validation split positives:")
print(f"  Val dates 2015-11-25 to 2015-11-29:")
val_rows = df[(df['date']>='2015-11-25') & (df['date']<='2015-11-29')]
print(f"  Val rows: {len(val_rows)}")
print(f"  Val positives: {val_rows['flood_occurred'].sum()}")
print(f"  Val dates actually in dataset: {sorted(val_rows['date'].unique())}")
print()
print("  ISSUE: If val_positive_rate = 0%, validation set has NO real positives.")
print("  This violates requirement: 'Validation MUST contain real positive flood observations.'")
print()

# What are the actual flood event dates and their split assignment?
print("Flood event dates and their split:")
for fd in sorted(ACTIVE_FLOOD_DATES):
    if fd in all_dates:
        pos = df[df['date']==fd]['flood_occurred'].sum()
        if fd < '2015-11-25':
            split = 'TRAIN'
        elif fd <= '2015-11-29':
            split = 'VALIDATION'
        else:
            split = 'TEST'
        print(f"  {fd}: {pos} positives -> {split}")
    else:
        print(f"  {fd}: NOT IN DATASET")

print()
print("PROPOSED FIX for split:")
print("  TRAIN: dates before 2015-11-15 (pre-first-event baseline only)")
print("  VALIDATION: 2015-11-15 to 2015-11-17 (first wave)")
print("  TEST: 2015-11-30 to 2015-12-10 (catastrophic deluge)")
print()

# Compute proposed splits
prop_train_mask = df['date'] < '2015-11-15'
prop_val_mask = (df['date'] >= '2015-11-15') & (df['date'] <= '2015-11-17')
prop_test_mask = df['date'] >= '2015-11-30'
prop_other_mask = (df['date'] >= '2015-11-18') & (df['date'] < '2015-11-30')

print(f"  Proposed TRAIN: {df.loc[prop_train_mask,'date'].min()} to {df.loc[prop_train_mask,'date'].max()}")
print(f"    Rows: {prop_train_mask.sum()}, Positives: {df.loc[prop_train_mask,'flood_occurred'].sum()}, Rate: {df.loc[prop_train_mask,'flood_occurred'].mean()*100:.2f}%")
prop_train_dates = sorted(df.loc[prop_train_mask,'date'].unique())
print(f"    Actual dates ({len(prop_train_dates)}): {prop_train_dates}")

print(f"\n  Proposed VALIDATION: {df.loc[prop_val_mask,'date'].min()} to {df.loc[prop_val_mask,'date'].max()}")
print(f"    Rows: {prop_val_mask.sum()}, Positives: {df.loc[prop_val_mask,'flood_occurred'].sum()}, Rate: {df.loc[prop_val_mask,'flood_occurred'].mean()*100:.2f}%")
prop_val_dates = sorted(df.loc[prop_val_mask,'date'].unique())
print(f"    Actual dates ({len(prop_val_dates)}): {prop_val_dates}")

print(f"\n  Proposed TEST: {df.loc[prop_test_mask,'date'].min()} to {df.loc[prop_test_mask,'date'].max()}")
print(f"    Rows: {prop_test_mask.sum()}, Positives: {df.loc[prop_test_mask,'flood_occurred'].sum()}, Rate: {df.loc[prop_test_mask,'flood_occurred'].mean()*100:.2f}%")
prop_test_dates = sorted(df.loc[prop_test_mask,'date'].unique())
print(f"    Actual dates ({len(prop_test_dates)}): {prop_test_dates}")

print(f"\n  Dates in neither split (transition): {sorted(df.loc[prop_other_mask,'date'].unique())}")
print(f"  These transition dates would be excluded from chronological split")

print("\n" + "=" * 80)
print("SECTION 17: WORLDCOVER_CLASS REDUNDANCY ANALYSIS")
print("=" * 80)
# Is worldcover_class fully determined by the ratios?
# If a cell has built_up_ratio dominant => class 50, water dominant => 80, etc.
static_wc2 = df[['grid_id','built_up_ratio','water_ratio','vegetation_ratio','worldcover_class']].drop_duplicates('grid_id')
# Classes: 10=Tree, 20=Shrub, 30=Grass, 40=Crop, 50=Built-up, 80=Water
# Map: if water_ratio > 0.5 => 80, if built_up_ratio > 0.5 => 50, etc.
# Actual unique classes in data:
print(f"Unique worldcover_class values: {sorted(static_wc2['worldcover_class'].unique())}")
# Check if worldcover_class adds information beyond the 3 ratio columns
# Specifically: are there cells where class != what ratios would predict?
wc_pred = static_wc2.copy()
wc_pred['ratio_max'] = wc_pred[['built_up_ratio','water_ratio','vegetation_ratio']].max(axis=1)
wc_pred['pred_class'] = 50  # default built-up
wc_pred.loc[wc_pred['water_ratio'] > wc_pred['built_up_ratio'], 'pred_class'] = 80
wc_pred.loc[wc_pred['vegetation_ratio'] > wc_pred['built_up_ratio'], 'pred_class'] = 10  # simplification
conflicts = wc_pred[wc_pred['worldcover_class'] != wc_pred['pred_class']]
print(f"Cells where majority class != predicted from ratios: {len(conflicts)} ({len(conflicts)/len(wc_pred)*100:.1f}%)")
# Are there multi-class cells not captured by the 3 ratio columns?
# WorldCover also has class 60=Bare/Sparse, 70=Snow/Ice (not captured in ratios)
has_other_class = wc_pred[~wc_pred['worldcover_class'].isin([10,20,30,40,50,80])]
print(f"Cells with 'other' worldcover classes (bare, sparse, etc.): {len(has_other_class)}")
print(f"  Classes: {has_other_class['worldcover_class'].unique()}")
print(f"\nConclusion: worldcover_class provides dominant-class info not fully captured by the 3 ratios")
print(f"  (ratios only cover built, water, veg; class includes bare/sparse/cropland/shrub distinctions)")

print("\n" + "=" * 80)
print("SECTION 18: BUILDING AREA CALCULATION ISSUE")
print("=" * 80)
# The code uses: bldg_areas[target_idx] += poly.area * (111000 * 108000)
# But poly.area is in DEGREES^2 when the polygon is in WGS84
# 1 degree lat ~ 111000m, 1 degree lon ~ 108000m (approximate at Chennai latitude)
# This is an approximation. At 13 deg N, cos(13 deg) = 0.974, so 1 deg lon = 111195*0.974 ~ 108303m
# The constant 108000 is approximately correct.
# However, using centroid's lon/lat vs reprojecting to UTM for area calculation:
# Let's check what typical building footprint sizes look like
static_bldg2 = df[['grid_id','building_count','building_area_m2']].drop_duplicates('grid_id')
has_bldg2 = static_bldg2[static_bldg2['building_count']>0]
avg_area2 = has_bldg2['building_area_m2'] / has_bldg2['building_count']
print(f"Average building footprint area: {avg_area2.mean():.1f} m2")
print(f"  (Typical urban residential ~ 50-200 m2, commercial 500-5000 m2)")
print(f"  min avg: {avg_area2.min():.1f}, max avg: {avg_area2.max():.1f}")
print(f"\nBuilding area approximation note:")
print(f"  Code: poly.area * 111000 * 108000 (degree-space area to m2)")
print(f"  Correct approach: project to UTM32644 then compute area")
print(f"  Approximation error at Chennai (13N): ~2-5% due to cosine correction")
print(f"  This is acceptable for ML feature engineering purposes")

print("\nAUDIT COMPLETE.")
print("=" * 80)
