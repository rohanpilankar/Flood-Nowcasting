"""
Spatial Grid Generation for Greater Mumbai.
Projects boundary to UTM Zone 43N (EPSG:32643) for accurate metric cell sizing,
generates a regular 500m grid, clips to Mumbai boundary, and attaches locality tags.
"""

import os
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box, mapping

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

# Mumbai reference localities with approximate centroid coordinates
LOCALITIES = [
    {"name": "Colaba / Fort", "lat": 18.915, "lon": 72.825},
    {"name": "Marine Lines / Kalbadevi", "lat": 18.945, "lon": 72.828},
    {"name": "Dadar East / Hindmata", "lat": 19.015, "lon": 72.844},
    {"name": "Worli / Prabhadevi", "lat": 19.012, "lon": 72.822},
    {"name": "Sion / King's Circle", "lat": 19.035, "lon": 72.860},
    {"name": "Dharavi / Mahim", "lat": 19.042, "lon": 72.848},
    {"name": "Bandra West", "lat": 19.055, "lon": 72.830},
    {"name": "Bandra Kurla Complex (BKC)", "lat": 19.065, "lon": 72.868},
    {"name": "Kurla West / LBS Marg", "lat": 19.072, "lon": 72.878},
    {"name": "Santacruz / Milan Subway", "lat": 19.083, "lon": 72.842},
    {"name": "Chembur East", "lat": 19.062, "lon": 72.900},
    {"name": "Ghatkopar West", "lat": 19.088, "lon": 72.910},
    {"name": "Andheri Subway / West", "lat": 19.120, "lon": 72.845},
    {"name": "Saki Naka / Andheri East", "lat": 19.108, "lon": 72.888},
    {"name": "Powai / Hiranandani", "lat": 19.125, "lon": 72.915},
    {"name": "Vikhroli East", "lat": 19.112, "lon": 72.935},
    {"name": "Jogeshwari / JVLR", "lat": 19.138, "lon": 72.855},
    {"name": "Goregaon West", "lat": 19.162, "lon": 72.842},
    {"name": "Malad West", "lat": 19.185, "lon": 72.838},
    {"name": "Kandivali West", "lat": 19.210, "lon": 72.835},
    {"name": "Borivali / Dahisar Subway", "lat": 19.255, "lon": 72.858},
    {"name": "Mulund West", "lat": 19.175, "lon": 72.950}
]


def generate_mumbai_grid(cell_size_m: int = 500):
    """Generates metric grid clipped to Mumbai boundary."""
    boundary_path = os.path.join(RAW_DIR, "boundary", "mumbai_boundary.geojson")
    boundary_gdf = gpd.read_file(boundary_path)

    # 1. Project to UTM Zone 43N (EPSG:32643) for metric grid operations
    utm_crs = "EPSG:32643"
    boundary_utm = boundary_gdf.to_crs(utm_crs)
    minx, miny, maxx, maxy = boundary_utm.total_bounds

    print(f"[*] Projecting to {utm_crs}. Bounding box: X[{minx:.1f}, {maxx:.1f}], Y[{miny:.1f}, {maxy:.1f}]")

    # 2. Construct grid polygon boxes
    x_coords = np.arange(minx, maxx, cell_size_m)
    y_coords = np.arange(miny, maxy, cell_size_m)

    grid_boxes = []
    for x in x_coords:
        for y in y_coords:
            grid_boxes.append(box(x, y, x + cell_size_m, y + cell_size_m))

    raw_grid_gdf = gpd.GeoDataFrame({"geometry": grid_boxes}, crs=utm_crs)
    print(f"[*] Initial square boxes generated: {len(raw_grid_gdf)}")

    # 3. Spatial intersection with Mumbai boundary
    clipped_grid = gpd.overlay(raw_grid_gdf, boundary_utm, how="intersection")
    print(f"[*] Clipped cells intersecting boundary: {len(clipped_grid)}")

    # 4. Filter out slivers (< 10% of cell area)
    min_area = (cell_size_m * cell_size_m) * 0.10
    clipped_grid = clipped_grid[clipped_grid.geometry.area >= min_area].copy()

    # 5. Transform back to EPSG:4326 for web and API consumption
    grid_wgs84 = clipped_grid.to_crs("EPSG:4326").copy()
    grid_wgs84.reset_index(drop=True, inplace=True)

    # 6. Assign unique Grid IDs and attributes
    grid_wgs84["grid_id"] = [f"MUM_{i+1:06d}" for i in range(len(grid_wgs84))]
    grid_wgs84["cell_size_m"] = cell_size_m
    grid_wgs84["area_sqkm"] = round(grid_wgs84.to_crs(utm_crs).geometry.area / 1e6, 4)

    # Calculate centroid coordinates in projected UTM CRS for metric accuracy, then convert to WGS84
    utm_centroids = clipped_grid.geometry.centroid.to_crs("EPSG:4326")
    grid_wgs84["centroid_lat"] = utm_centroids.y.round(6)
    grid_wgs84["centroid_lon"] = utm_centroids.x.round(6)

    # Attach closest reference locality
    def find_locality(lat, lon):
        best_name = "Mumbai Central"
        min_dist = float("inf")
        for loc in LOCALITIES:
            d = (lat - loc["lat"]) ** 2 + (lon - loc["lon"]) ** 2
            if d < min_dist:
                min_dist = d
                best_name = loc["name"]
        return best_name

    grid_wgs84["locality"] = [
        find_locality(row["centroid_lat"], row["centroid_lon"])
        for _, row in grid_wgs84.iterrows()
    ]

    # Save to GeoJSON and Parquet
    out_dir = os.path.join(PROCESSED_DIR, "grids")
    os.makedirs(out_dir, exist_ok=True)

    geojson_path = os.path.join(out_dir, f"mumbai_grid_{cell_size_m}m.geojson")
    grid_wgs84[["grid_id", "locality", "centroid_lat", "centroid_lon", "area_sqkm", "geometry"]].to_file(geojson_path, driver="GeoJSON")

    parquet_path = os.path.join(out_dir, f"mumbai_grid_{cell_size_m}m.parquet")
    grid_wgs84[["grid_id", "locality", "centroid_lat", "centroid_lon", "area_sqkm", "geometry"]].to_parquet(parquet_path)

    print(f"[OK] Saved spatial grid ({len(grid_wgs84)} sectors): {geojson_path}")
    print(f"[OK] Saved parquet spatial grid: {parquet_path}")
    return grid_wgs84


if __name__ == "__main__":
    generate_mumbai_grid(500)
