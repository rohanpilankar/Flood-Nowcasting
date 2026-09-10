"""
Scientific Audit Investigation Script for Chennai ML Dataset.
Audits all 12 points raised in the final audit checklist.
"""

import os
import json
import gzip
import zipfile
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.windows import from_bounds
import shapely
from shapely.geometry import Point, box

BASE_DIR = r"g:\fl2"
RAW_DIR = os.path.join(BASE_DIR, "Data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "Data", "processed")
FINAL_DIR = os.path.join(BASE_DIR, "Data", "final")

def audit_all():
    results = {}
    
    # Load final parquet
    parquet_path = os.path.join(FINAL_DIR, "chennai_flood_training.parquet")
    print(f"Loading final dataset: {parquet_path}")
    df = pd.read_parquet(parquet_path)
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # ----------------------------------------------------
    # 1. Target Validity
    # ----------------------------------------------------
    print("\n--- 1. Target Validity ---")
    clean_zip = os.path.join(RAW_DIR, "FloodWatch_Clean_GeoJSON.zip")
    f2015_gdf = gpd.read_file(f"/vsizip/{clean_zip.replace('\\', '/')}/Chennai_Flooding_Points_2015.geojson")
    inund_gdf = gpd.read_file(f"/vsizip/{clean_zip.replace('\\', '/')}/Chennai_Inundation_Depth.geojson")
    print(f"Chennai_Flooding_Points_2015 feature count: {len(f2015_gdf)}")
    print(f"Chennai_Inundation_Depth feature count: {len(inund_gdf)}")
    print(f"Total flood point observations: {len(f2015_gdf) + len(inund_gdf)}")
    
    # Unique flooded cells in dataset
    flooded_cells = df[df["flood_occurred"] == 1]["grid_id"].unique()
    print(f"Unique grid cells with flood_occurred=1: {len(flooded_cells)}")
    print(f"Total rows with flood_occurred=1: {(df['flood_occurred'] == 1).sum()}")
    print(f"Total rows with flood_occurred=0: {(df['flood_occurred'] == 0).sum()}")
    print(f"Positive rate: {df['flood_occurred'].mean() * 100:.2f}%")
    
    # Dates on which flood_occurred=1 occurs
    pos_dates = df[df["flood_occurred"] == 1]["date"].value_counts().to_dict()
    print(f"Dates with flood_occurred=1: {pos_dates}")
    
    # Check if any flood_occurred=1 on non-active dates
    active_flood_dates = {
        "2015-11-15", "2015-11-16", "2015-11-17",
        "2015-11-30", "2015-12-01", "2015-12-02", "2015-12-03", "2015-12-04"
    }
    non_active_pos = df[(~df["date"].isin(active_flood_dates)) & (df["flood_occurred"] == 1)]
    print(f"Non-active date positives: {len(non_active_pos)}")
    
    # Absence of observation vs genuine negatives:
    # On flood dates, how many cells are 0?
    flood_date_negatives = df[(df["date"].isin(active_flood_dates)) & (df["flood_occurred"] == 0)]
    print(f"Flood date 0s (unlabeled / absence of recorded flood point): {len(flood_date_negatives)}")
    # On non-flood dates, how many cells are 0?
    non_flood_date_negatives = df[(~df["date"].isin(active_flood_dates)) & (df["flood_occurred"] == 0)]
    print(f"Non-flood date 0s (physically confirmed baseline non-flood): {len(non_flood_date_negatives)}")
    
    # ----------------------------------------------------
    # 2. Temporal Validity
    # ----------------------------------------------------
    print("\n--- 2. Temporal Validity ---")
    rain_path = os.path.join(RAW_DIR, "Chennai rainfall.csv")
    df_rain = pd.read_csv(rain_path)
    df_rain["parsed_date"] = pd.to_datetime(df_rain["Date"], format="%d-%m-%Y")
    unique_rain_dates = df_rain["parsed_date"].dt.strftime("%Y-%m-%d").unique()
    ds_dates = sorted(df["date"].unique())
    print(f"Number of dates in dataset: {len(ds_dates)}")
    print(f"Date range: {ds_dates[0]} to {ds_dates[-1]}")
    all_dates_in_rain = all(d in unique_rain_dates for d in ds_dates)
    print(f"Are all dataset dates present in Chennai rainfall.csv? {all_dates_in_rain}")
    
    # Check rolling rainfall monotonicity/consistency
    # rainfall_cum_2d_mm >= rainfall_daily_mm (except floating point roundoff)
    viol_2d = (df["rainfall_cum_2d_mm"] < df["rainfall_daily_mm"] - 0.05).sum()
    viol_3d = (df["rainfall_cum_3d_mm"] < df["rainfall_cum_2d_mm"] - 0.05).sum()
    viol_7d = (df["rainfall_cum_7d_mm"] < df["rainfall_cum_3d_mm"] - 0.05).sum()
    print(f"Violations cum_2d < daily: {viol_2d}")
    print(f"Violations cum_3d < cum_2d: {viol_3d}")
    print(f"Violations cum_7d < cum_3d: {viol_7d}")
    
    # ----------------------------------------------------
    # 3. Spatial Validity & Grid Geometry
    # ----------------------------------------------------
    print("\n--- 3. Spatial Validity ---")
    grid_path = os.path.join(PROCESSED_DIR, "grids", "chennai_grid_500m.parquet")
    grid_gdf = gpd.read_parquet(grid_path)
    print(f"Grid CRS: {grid_gdf.crs}")
    print(f"Grid cell count: {len(grid_gdf)}")
    print(f"Grid bounds (UTM): {grid_gdf.total_bounds}")
    grid_gdf_wgs = grid_gdf.to_crs("EPSG:4326")
    print(f"Grid bounds (WGS84): {grid_gdf_wgs.total_bounds}")
    
    # Check cell dimensions
    areas = grid_gdf.geometry.area
    print(f"Cell areas min={areas.min()}, max={areas.max()}, mean={areas.mean()} (expected 250,000 m2)")
    
    # Check ocean cells
    # Check if any cell has water_ratio > 0.95 and built_up == 0 in Bay of Bengal
    coastal_water = df[df["water_ratio"] > 0.9]
    print(f"Cells with water_ratio > 0.9: {coastal_water['grid_id'].nunique()}")
    print(coastal_water[["grid_id", "longitude", "latitude", "water_ratio", "built_up_ratio", "elevation_m"]].drop_duplicates().head(10))
    
    # ----------------------------------------------------
    # 4. Drainage Completeness
    # ----------------------------------------------------
    print("\n--- 4. Drainage Completeness ---")
    drain_names = [
        "Chennai_Storm_Water_Drains_2023.geojson",
        "Chennai_Basin_Macro_Drains.geojson",
        "Chennai_Basin_Micro_Drains.geojson",
        "Chennai_Basin_Rivers_Streams.geojson",
        "Chennai_Buckingham_Canal.geojson",
        "Chennai_Krishna_Water_Canal.geojson"
    ]
    with zipfile.ZipFile(clean_zip, "r") as z:
        for dn in drain_names:
            vpath = f"/vsizip/{clean_zip.replace('\\', '/')}/{dn}"
            dgdf = gpd.read_file(vpath)
            print(f"{dn}: {len(dgdf)} features, CRS={dgdf.crs}, bounds={dgdf.total_bounds}")
            
    # Check dist_to_krishna_water_canal_m in dataset
    print(f"dist_to_krishna_water_canal_m min={df['dist_to_krishna_water_canal_m'].min()}, max={df['dist_to_krishna_water_canal_m'].max()}, mean={df['dist_to_krishna_water_canal_m'].mean()}")
    print(f"drainage_density_m_per_km2 min={df['drainage_density_m_per_km2'].min()}, max={df['drainage_density_m_per_km2'].max()}, mean={df['drainage_density_m_per_km2'].mean()}")
    
    # ----------------------------------------------------
    # 5. DEM Validity
    # ----------------------------------------------------
    print("\n--- 5. DEM Validity ---")
    dem_raw = os.path.join(RAW_DIR, "Chennai_Copernicus_GLO30_DEM.tif")
    with rasterio.open(dem_raw) as src:
        print(f"Raw DEM CRS: {src.crs}, res={src.res}, bounds={src.bounds}, nodata={src.nodata}")
        tags = src.tags()
        print(f"DEM tags: {tags}")
    print(f"elevation_m: min={df['elevation_m'].min()}, max={df['elevation_m'].max()}, mean={df['elevation_m'].mean()}")
    print(f"slope_deg: min={df['slope_deg'].min()}, max={df['slope_deg'].max()}, mean={df['slope_deg'].mean()}")
    print(f"low_lying_score: min={df['low_lying_score'].min()}, max={df['low_lying_score'].max()}, mean={df['low_lying_score'].mean()}")
    
    # ----------------------------------------------------
    # 6. Soil Validity
    # ----------------------------------------------------
    print("\n--- 6. Soil Validity ---")
    soil_raw = os.path.join(RAW_DIR, "Chennai_SoilGrids_Clay_0_5cm.tif")
    with rasterio.open(soil_raw) as src:
        print(f"Raw SoilGrids CRS: {src.crs}, res={src.res}, bounds={src.bounds}, nodata={src.nodata}")
        arr = src.read(1)
        valid_px = arr[(arr != src.nodata) & (arr > 0)]
        print(f"Raw SoilGrids pixel range: min={valid_px.min()}, max={valid_px.max()}, mean={valid_px.mean()}")
    
    # Check soil in processed static features
    static_p = os.path.join(PROCESSED_DIR, "features", "chennai_static_spatial_features.parquet")
    sdf = pd.read_parquet(static_p)
    print(f"soil_clay_0_5cm in static: min={sdf['soil_clay_0_5cm'].min()}, max={sdf['soil_clay_0_5cm'].max()}, mean={sdf['soil_clay_0_5cm'].mean()}")
    
    # Check how many were native vs interpolated
    soil_utm = os.path.join(PROCESSED_DIR, "rasters", "chennai_soil_clay_250m_utm44n.tif")
    with rasterio.open(soil_utm) as src:
        sample_pts = [(r.x_utm, r.y_utm) for _, r in sdf.iterrows()]
        sampled = [v[0] for v in src.sample(sample_pts)]
        sampled_arr = np.array(sampled)
        nodata_cnt = np.sum((sampled_arr == src.nodata) | (sampled_arr <= 0))
        valid_cnt = len(sampled_arr) - nodata_cnt
        print(f"Soil at grid centroids: {valid_cnt} valid ({valid_cnt/len(sdf)*100:.1f}%), {nodata_cnt} nodata/unmapped ({nodata_cnt/len(sdf)*100:.1f}%)")
        
    # ----------------------------------------------------
    # 7. Building Validity
    # ----------------------------------------------------
    print("\n--- 7. Building Validity ---")
    bldg_files = [
        "Chennai_Building_Footprints_Microsoft_GML_123312201.csv.gz",
        "Chennai_Building_Footprints_Microsoft_GML_123312203.csv.gz",
        "Chennai_Building_Footprints_Microsoft_GML_123312210.csv.gz",
        "Chennai_Building_Footprints_Microsoft_GML_123312212.csv.gz"
    ]
    tot_lines = 0
    for bf in bldg_files:
        cnt = 0
        with gzip.open(os.path.join(RAW_DIR, bf), "rt", encoding="utf-8") as f:
            for _ in f:
                cnt += 1
        print(f"{bf}: {cnt:,} footprints")
        tot_lines += cnt
    print(f"Total raw footprints across 4 files: {tot_lines:,}")
    print(f"building_count in dataset: sum={sdf['building_count'].sum():,}, max={sdf['building_count'].max()}, mean={sdf['building_count'].mean():.1f}")
    print(f"building_area_m2 in dataset: sum={sdf['building_area_m2'].sum():,}, max={sdf['building_area_m2'].max()}, mean={sdf['building_area_m2'].mean():.1f}")
    
    # ----------------------------------------------------
    # 8. Infrastructure Validity
    # ----------------------------------------------------
    print("\n--- 8. Infrastructure Validity ---")
    crit_p = os.path.join(RAW_DIR, "Chennai_Critical_Infrastructure_OSM.geojson")
    gdf_crit = gpd.read_file(crit_p)
    print(f"Total critical infra features: {len(gdf_crit)}")
    print(f"Amenity value counts:\n{gdf_crit['amenity'].value_counts()}")
    print(f"dist_to_hospital_m: min={sdf['dist_to_hospital_m'].min()}, max={sdf['dist_to_hospital_m'].max()}, mean={sdf['dist_to_hospital_m'].mean():.1f}")
    print(f"hospital_count_1km: min={sdf['hospital_count_1km'].min()}, max={sdf['hospital_count_1km'].max()}, mean={sdf['hospital_count_1km'].mean():.1f}")
    print(f"dist_to_fire_station_m: min={sdf['dist_to_fire_station_m'].min()}, max={sdf['dist_to_fire_station_m'].max()}, mean={sdf['dist_to_fire_station_m'].mean():.1f}")
    print(f"dist_to_police_m: min={sdf['dist_to_police_m'].min()}, max={sdf['dist_to_police_m'].max()}, mean={sdf['dist_to_police_m'].mean():.1f}")

    # ----------------------------------------------------
    # 9. Leakage & Correlation Check
    # ----------------------------------------------------
    print("\n--- 9. Leakage & Correlation Check ---")
    predictors = [c for c in df.columns if c not in ["grid_id", "date", "latitude", "longitude", "x_utm", "y_utm", "flood_occurred"]]
    corrs = df[predictors].apply(lambda s: s.corr(df["flood_occurred"])).to_dict()
    print("Correlations with flood_occurred:")
    for k, v in sorted(corrs.items(), key=lambda item: abs(item[1]), reverse=True):
        print(f"  {k:32s}: {v:.4f}")

    # ----------------------------------------------------
    # 10. Splits Check
    # ----------------------------------------------------
    print("\n--- 10. Splits Check ---")
    splits_p = os.path.join(FINAL_DIR, "train_test_splits.json")
    with open(splits_p, "r") as f:
        sp = json.load(f)
    print(json.dumps(sp, indent=2))

if __name__ == "__main__":
    audit_all()
