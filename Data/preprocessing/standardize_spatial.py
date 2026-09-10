"""
Step 2: Spatial Data Standardization for Chennai Urban Flood Nowcasting.
Reprojects vectors to EPSG:32644 (UTM 44N), validates geometries,
and standardizes/clips raster assets (DEM, SoilGrids, WorldCover).
Outputs saved to Data/processed/vectors/ and Data/processed/rasters/.
"""

import os
import zipfile
import logging
import numpy as np
import geopandas as gpd
from shapely.validation import make_valid
from shapely.geometry import box
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.windows import from_bounds

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("StandardizeSpatial")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_DIR = os.path.join(BASE_DIR, "Data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "Data", "processed")
VECTORS_DIR = os.path.join(PROCESSED_DIR, "vectors")
RASTERS_DIR = os.path.join(PROCESSED_DIR, "rasters")

TARGET_CRS = "EPSG:32644" # WGS 84 / UTM Zone 44N (Metric, optimal for Chennai ~13N, 80.2E)
STUDY_BOUNDS_WGS84 = (80.10, 12.85, 80.35, 13.25) # minx, miny, maxx, maxy


def standardize_vectors():
    logger.info("Standardizing vector layers to %s...", TARGET_CRS)
    os.makedirs(VECTORS_DIR, exist_ok=True)
    study_bbox_geom = box(*STUDY_BOUNDS_WGS84)
    study_gdf = gpd.GeoDataFrame(geometry=[study_bbox_geom], crs="EPSG:4326").to_crs(TARGET_CRS)
    study_poly = study_gdf.geometry.iloc[0]

    clean_zip = os.path.join(RAW_DIR, "FloodWatch_Clean_GeoJSON.zip")
    if os.path.exists(clean_zip):
        with zipfile.ZipFile(clean_zip, "r") as z:
            for name in z.namelist():
                vpath = f"/vsizip/{clean_zip.replace(chr(92), '/')}/{name}"
                gdf = gpd.read_file(vpath)
                logger.info(f"Processing {name}: {len(gdf)} features, CRS={gdf.crs}")

                # Ensure CRS
                if gdf.crs is None:
                    gdf = gdf.set_crs("EPSG:4326")
                
                # Make valid
                gdf["geometry"] = gdf["geometry"].apply(lambda g: make_valid(g) if g is not None and not g.is_valid else g)
                
                # Reproject to UTM 44N
                gdf = gdf.to_crs(TARGET_CRS)

                # Explode GeometryCollections if any line/point layer
                if "GeometryCollection" in gdf.geom_type.values:
                    gdf = gdf.explode(ignore_index=True)

                out_name = name.replace(".geojson", ".parquet")
                out_path = os.path.join(VECTORS_DIR, out_name)
                gdf.to_parquet(out_path)
                logger.info(f"Saved standardized vector: {out_path} ({len(gdf)} features)")

    # Critical Infrastructure
    crit_path = os.path.join(RAW_DIR, "Chennai_Critical_Infrastructure_OSM.geojson")
    if os.path.exists(crit_path):
        gdf_crit = gpd.read_file(crit_path)
        if gdf_crit.crs is None:
            gdf_crit = gdf_crit.set_crs("EPSG:4326")
        gdf_crit["geometry"] = gdf_crit["geometry"].apply(lambda g: make_valid(g) if g is not None and not g.is_valid else g)
        gdf_crit = gdf_crit.to_crs(TARGET_CRS)
        # Clip to study area
        gdf_crit = gdf_crit[gdf_crit.geometry.intersects(study_poly)].copy()
        out_path = os.path.join(VECTORS_DIR, "chennai_critical_infrastructure.parquet")
        gdf_crit.to_parquet(out_path)
        logger.info(f"Saved critical infrastructure: {out_path} ({len(gdf_crit)} features)")


def standardize_rasters():
    logger.info("Standardizing raster layers to %s...", TARGET_CRS)
    os.makedirs(RASTERS_DIR, exist_ok=True)
    minx, miny, maxx, maxy = STUDY_BOUNDS_WGS84

    # 1. Copernicus DEM GLO-30
    dem_raw = os.path.join(RAW_DIR, "Chennai_Copernicus_GLO30_DEM.tif")
    dem_out = os.path.join(RASTERS_DIR, "chennai_dem_30m_utm44n.tif")
    if os.path.exists(dem_raw):
        logger.info("Reprojecting DEM to UTM 44N (30m bilinear)...")
        with rasterio.open(dem_raw) as src:
            transform, width, height = calculate_default_transform(
                src.crs, TARGET_CRS, src.width, src.height, *src.bounds, resolution=30.0
            )
            profile = src.profile.copy()
            profile.update({
                "crs": TARGET_CRS,
                "transform": transform,
                "width": width,
                "height": height,
                "nodata": -9999.0
            })
            with rasterio.open(dem_out, "w", **profile) as dst:
                reproject(
                    source=rasterio.band(src, 1),
                    destination=rasterio.band(dst, 1),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=TARGET_CRS,
                    resampling=Resampling.bilinear,
                    dst_nodata=-9999.0
                )
        logger.info(f"Saved standardized DEM: {dem_out}")

    # 2. SoilGrids Clay 0-5cm
    soil_raw = os.path.join(RAW_DIR, "Chennai_SoilGrids_Clay_0_5cm.tif")
    soil_out = os.path.join(RASTERS_DIR, "chennai_soil_clay_250m_utm44n.tif")
    if os.path.exists(soil_raw):
        logger.info("Reprojecting SoilGrids Clay to UTM 44N (250m bilinear)...")
        with rasterio.open(soil_raw) as src:
            transform, width, height = calculate_default_transform(
                src.crs, TARGET_CRS, src.width, src.height, *src.bounds, resolution=250.0
            )
            profile = src.profile.copy()
            profile.update({
                "crs": TARGET_CRS,
                "transform": transform,
                "width": width,
                "height": height,
                "nodata": -1
            })
            with rasterio.open(soil_out, "w", **profile) as dst:
                reproject(
                    source=rasterio.band(src, 1),
                    destination=rasterio.band(dst, 1),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=TARGET_CRS,
                    resampling=Resampling.bilinear,
                    dst_nodata=-1
                )
        logger.info(f"Saved standardized SoilGrids: {soil_out}")

    # 3. ESA WorldCover 2021 (Windowed extract + Nearest Neighbour)
    wc_zip = os.path.join(RAW_DIR, "Chennai_WorldCover_2021_v200.zip")
    wc_out = os.path.join(RASTERS_DIR, "chennai_worldcover_10m_utm44n.tif")
    if os.path.exists(wc_zip):
        logger.info("Window-reading ESA WorldCover 2021 over Chennai and warping to UTM 44N (10m nearest)...")
        vsi_path = "/vsizip/" + wc_zip.replace("\\", "/") + "/ESA_WorldCover_10m_2021_v200_N12E078_Map.tif"
        with rasterio.open(vsi_path) as src:
            # Buffer bounds slightly for seamless coverage
            win = from_bounds(minx - 0.05, miny - 0.05, maxx + 0.05, maxy + 0.05, src.transform)
            arr = src.read(1, window=win)
            win_transform = rasterio.windows.transform(win, src.transform)

            transform, width, height = calculate_default_transform(
                src.crs, TARGET_CRS, arr.shape[1], arr.shape[0],
                left=minx - 0.05, bottom=miny - 0.05, right=maxx + 0.05, top=maxy + 0.05,
                resolution=10.0
            )
            profile = src.profile.copy()
            profile.update({
                "crs": TARGET_CRS,
                "transform": transform,
                "width": width,
                "height": height,
                "nodata": 0
            })
            with rasterio.open(wc_out, "w", **profile) as dst:
                reproject(
                    source=arr,
                    destination=rasterio.band(dst, 1),
                    src_transform=win_transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=TARGET_CRS,
                    resampling=Resampling.nearest,
                    dst_nodata=0
                )
        logger.info(f"Saved standardized WorldCover: {wc_out}")


def run_standardization():
    standardize_vectors()
    standardize_rasters()


if __name__ == "__main__":
    run_standardization()
