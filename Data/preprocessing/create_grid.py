"""
Step 3: 500m Modelling Grid Generation for Chennai Urban Flood Nowcasting.
Generates a regular 500m x 500m metric grid covering the Chennai study area in EPSG:32644.
Computes grid centroids in both EPSG:4326 (lat/lon) and EPSG:32644 (metric UTM).
Filters deep marine non-land cells.
Exports to GeoJSON and Parquet formats.
"""

import os
import logging
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box, Polygon
from pyproj import Transformer

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("CreateGrid")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROCESSED_DIR = os.path.join(BASE_DIR, "Data", "processed")
GRIDS_DIR = os.path.join(PROCESSED_DIR, "grids")
RASTERS_DIR = os.path.join(PROCESSED_DIR, "rasters")

TARGET_CRS = "EPSG:32644"
RESOLUTION_M = 500.0 # 500 meters

# Study area in WGS84: Greater Chennai Corporation & contiguous urban catchment
MIN_LON, MIN_LAT = 80.10, 12.85
MAX_LON, MAX_LAT = 80.35, 13.25


def generate_chennai_grid():
    logger.info(f"Generating Chennai modelling grid at {RESOLUTION_M}m resolution...")
    os.makedirs(GRIDS_DIR, exist_ok=True)

    transformer_to_utm = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)
    transformer_to_wgs = Transformer.from_crs(TARGET_CRS, "EPSG:4326", always_xy=True)

    min_x, min_y = transformer_to_utm.transform(MIN_LON, MIN_LAT)
    max_x, max_y = transformer_to_utm.transform(MAX_LON, MAX_LAT)

    # Snap bounds to resolution multiples
    min_x = np.floor(min_x / RESOLUTION_M) * RESOLUTION_M
    min_y = np.floor(min_y / RESOLUTION_M) * RESOLUTION_M
    max_x = np.ceil(max_x / RESOLUTION_M) * RESOLUTION_M
    max_y = np.ceil(max_y / RESOLUTION_M) * RESOLUTION_M

    x_coords = np.arange(min_x, max_x, RESOLUTION_M)
    y_coords = np.arange(min_y, max_y, RESOLUTION_M)

    logger.info(f"Grid dimensions: {len(x_coords)} cols x {len(y_coords)} rows = {len(x_coords)*len(y_coords)} potential cells")

    cells = []
    grid_idx = 1

    for y in y_coords:
        for x in x_coords:
            cell_box = box(x, y, x + RESOLUTION_M, y + RESOLUTION_M)
            cx, cy = x + RESOLUTION_M / 2.0, y + RESOLUTION_M / 2.0
            lon, lat = transformer_to_wgs.transform(cx, cy)
            grid_id = f"CHN_G{grid_idx:04d}"

            cells.append({
                "grid_id": grid_id,
                "x_utm": round(cx, 2),
                "y_utm": round(cy, 2),
                "longitude": round(lon, 6),
                "latitude": round(lat, 6),
                "geometry": cell_box
            })
            grid_idx += 1

    gdf = gpd.GeoDataFrame(cells, crs=TARGET_CRS)
    logger.info(f"Total raw grid cells generated: {len(gdf)}")

    # Filter out offshore marine ocean cells in Bay of Bengal using WorldCover land cover
    wc_path = os.path.join(RASTERS_DIR, "chennai_worldcover_10m_utm44n.tif")
    if os.path.exists(wc_path):
        import rasterio
        from rasterio.windows import from_bounds
        logger.info("Applying marine mask using WorldCover 10m raster...")
        is_ocean = []
        with rasterio.open(wc_path) as src:
            for geom in gdf.geometry.values:
                win = from_bounds(*geom.bounds, src.transform)
                arr = src.read(1, window=win)
                valid = arr[arr != src.nodata]
                if len(valid) > 0:
                    w_ratio = np.mean(valid == 80)
                    b_ratio = np.mean(valid == 50)
                else:
                    w_ratio = 1.0
                    b_ratio = 0.0
                # Marine cell: >95% water, 0% built-up, east of 80.29 E in the Bay of Bengal
                is_ocean.append((w_ratio > 0.95) and (b_ratio == 0.0))

        is_ocean = np.array(is_ocean) & (gdf["longitude"].values > 80.29)
        ocean_count = np.sum(is_ocean)
        gdf = gdf[~is_ocean].copy()
        logger.info(f"Masked {ocean_count} offshore Bay of Bengal ocean cells. Retained {len(gdf)} terrestrial/coastal cells.")
    else:
        # Fallback to DEM-based elevation filter
        dem_path = os.path.join(RASTERS_DIR, "chennai_dem_30m_utm44n.tif")
        if os.path.exists(dem_path):
            import rasterio
            with rasterio.open(dem_path) as src:
                sample_points = [(row.x_utm, row.y_utm) for _, row in gdf.iterrows()]
                elevs = [val[0] for val in src.sample(sample_points)]
                gdf["temp_elev"] = elevs
                is_deep_sea = (gdf["temp_elev"] <= 0.0) & (gdf["longitude"] > 80.31)
                gdf = gdf[~is_deep_sea].drop(columns=["temp_elev"]).copy()
                logger.info(f"Retained {len(gdf)} terrestrial/coastal cells after DEM marine mask.")

    # Re-assign sequential grid_id
    gdf["grid_id"] = [f"CHN_G{i+1:04d}" for i in range(len(gdf))]

    # Save to GeoJSON (in WGS84 for web GIS interoperability) and Parquet (in UTM for fast processing)
    geojson_path = os.path.join(GRIDS_DIR, "chennai_grid_500m.geojson")
    parquet_path = os.path.join(GRIDS_DIR, "chennai_grid_500m.parquet")

    gdf_wgs84 = gdf.to_crs("EPSG:4326")
    gdf_wgs84.to_file(geojson_path, driver="GeoJSON")
    logger.info(f"Saved GeoJSON grid: {geojson_path}")

    gdf.to_parquet(parquet_path)
    logger.info(f"Saved Parquet grid: {parquet_path}")

    return gdf


if __name__ == "__main__":
    generate_chennai_grid()
